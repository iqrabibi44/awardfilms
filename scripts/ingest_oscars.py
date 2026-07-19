import os
import sys
import argparse
import logging
import re
import pandas as pd
import mysql.connector
from mysql.connector import Error as MySQLError
from tqdm import tqdm

# Use custom slugify if python-slugify isn't loaded
try:
    from slugify import slugify
except ImportError:
    import unicodedata
    def slugify(text):
        text = str(text)
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text).strip('-')
        return text

# Add project root to sys.path so we can import lib.text_spinner
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
from lib.text_spinner import TextParaphraser

# Set up logging
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "ingest_errors.log"),
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ─── MySQL / XAMPP credentials ────────────────────────────────────────────────
MYSQL_CONFIG = {
    "host":       "127.0.0.1",
    "port":       3306,
    "user":       "root",
    "password":   "",
    "database":   "awardfilms_db",
    "charset":    "utf8mb4",
    "use_unicode": True,
    "autocommit": False,
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except MySQLError as e:
        print(f"[-] ERROR: Could not connect to MySQL: {e}")
        sys.exit(1)

def get_or_create_oscar_ceremony(conn):
    cur = conn.cursor()
    try:
        # Check if oscars ceremony exists
        cur.execute("SELECT id FROM ceremonies WHERE slug = 'oscars'")
        row = cur.fetchone()
        if row:
            return row[0]
        
        # Insert if it doesn't exist
        cur.execute(
            """
            INSERT INTO ceremonies (slug, name, short_name, country, founded_year, frequency)
            VALUES ('oscars', 'Academy Awards', 'Oscars', 'United States', 1929, 'annual')
            """
        )
        ceremony_id = cur.lastrowid
        conn.commit()
        return ceremony_id
    finally:
        cur.close()

def parse_edition_number(ceremony_val):
    try:
        # Extract digits from ceremony value, e.g. "96" or "96th"
        match = re.search(r'\d+', str(ceremony_val))
        if match:
            return int(match.group())
    except Exception as e:
        logging.error(f"Error parsing ceremony number from '{ceremony_val}': {e}")
    return None

def main():
    parser = argparse.ArgumentParser(description="Ingest Oscar nominations from Kaggle CSV")
    parser.add_argument("--csv", required=True, help="Path to the Oscar awards CSV file")
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f"Error: CSV file not found at {args.csv}")
        sys.exit(1)

    print("Reading CSV dataset...")
    df = pd.read_csv(args.csv)
    
    # Required columns check
    required_cols = {'year_film', 'year_ceremony', 'ceremony', 'category', 'name', 'film', 'winner'}
    if not required_cols.issubset(df.columns):
        print(f"Error: CSV must contain these columns: {required_cols}")
        sys.exit(1)

    # Connect to db
    conn = get_db_connection()
    ceremony_id = get_or_create_oscar_ceremony(conn)

    print("Pre-processing data...")
    # Cache mapping dicts to reduce database hits and do batch inserts
    editions_cache = {}    # (ceremony_id, year) -> id
    categories_cache = {}  # (ceremony_id, slug) -> id
    films_cache = {}       # slug -> id

    # 1. Populate editions
    print("Upserting editions...")
    unique_editions = df[['year_ceremony', 'ceremony']].drop_duplicates()
    edition_rows = []
    for _, row in unique_editions.iterrows():
        year = int(row['year_ceremony'])
        edition_number = parse_edition_number(row['ceremony'])
        slug = f"{edition_number}th" if edition_number else str(year)
        edition_rows.append((ceremony_id, edition_number, year, slug))
    
    cur = conn.cursor()
    try:
        cur.executemany(
            """
            INSERT INTO editions (ceremony_id, edition_number, year, slug)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE edition_number = VALUES(edition_number), slug = VALUES(slug)
            """,
            edition_rows
        )
        conn.commit()
    finally:
        cur.close()
    
    # Re-fetch edition IDs into cache
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, ceremony_id, year FROM editions WHERE ceremony_id = %s", (ceremony_id,))
        for eid, cid, yr in cur.fetchall():
            editions_cache[(cid, yr)] = eid
    finally:
        cur.close()

    # 2. Populate categories
    print("Upserting categories...")
    unique_categories = df['category'].unique()
    cat_rows = []
    for cat_name in unique_categories:
        cat_name_str = str(cat_name).strip()
        cat_slug = slugify(cat_name_str)
        if not cat_slug:
            continue
        
        # Simple heuristic for department
        dept = 'Other'
        cat_lower = cat_name_str.lower()
        if 'actor' in cat_lower or 'actress' in cat_lower or 'performance' in cat_lower:
            dept = 'Acting'
        elif 'direct' in cat_lower:
            dept = 'Directing'
        elif 'write' in cat_lower or 'screenplay' in cat_lower or 'story' in cat_lower:
            dept = 'Writing'
        elif 'cinematography' in cat_lower:
            dept = 'Cinematography'
        elif 'edit' in cat_lower:
            dept = 'Editing'
        elif 'music' in cat_lower or 'song' in cat_lower or 'score' in cat_lower:
            dept = 'Music'
        elif 'sound' in cat_lower:
            dept = 'Sound'
        elif 'art' in cat_lower or 'production design' in cat_lower:
            dept = 'Art Direction'
        elif 'costume' in cat_lower:
            dept = 'Costume Design'
        elif 'effects' in cat_lower:
            dept = 'Visual Effects'
        elif 'documentary' in cat_lower:
            dept = 'Documentary'
        elif 'short' in cat_lower:
            dept = 'Short Film'

        is_craft = dept not in ['Acting', 'Directing', 'Writing', 'Other']
        # Only add if slug not already seen (dedup within batch)
        if (ceremony_id, cat_slug) not in {(r[0], r[1]) for r in cat_rows}:
            cat_rows.append((ceremony_id, cat_slug, cat_name_str, dept, int(is_craft)))
    
    cur = conn.cursor()
    try:
        cur.executemany(
            """
            INSERT INTO categories (ceremony_id, slug, name, department, is_craft)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE name = VALUES(name), department = VALUES(department), is_craft = VALUES(is_craft)
            """,
            cat_rows
        )
        conn.commit()
    finally:
        cur.close()
    
    # Re-fetch category IDs into cache
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, ceremony_id, slug FROM categories WHERE ceremony_id = %s", (ceremony_id,))
        for cid, cerid, sl in cur.fetchall():
            categories_cache[(cerid, sl)] = cid
    finally:
        cur.close()

    # 3. Populate films
    print("Upserting films (batch insert)...")
    # Some films are null or NaN, fill them
    df['film'] = df['film'].fillna("").astype(str).str.strip()
    df = df[df['film'] != ""] # Skip empty film rows
    
    unique_films = df[['film', 'year_film']].drop_duplicates()
    film_rows = []
    for _, row in unique_films.iterrows():
        title = str(row['film']).strip()
        year = int(row['year_film'])
        film_slug = slugify(f"{title} {year}")
        if not film_slug:
            continue
        # Dedup by slug within batch
        if film_slug not in {r[0] for r in film_rows}:
            film_rows.append((film_slug, title, year))
    
    # Insert in batches of 500 to avoid any limits
    BATCH = 500
    print(f"Inserting {len(film_rows)} unique films in batches of {BATCH}...")
    for i in tqdm(range(0, len(film_rows), BATCH), desc="Film batches"):
        batch = film_rows[i:i+BATCH]
        cur = conn.cursor()
        try:
            cur.executemany(
                """
                INSERT INTO films (slug, title, year)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE title = VALUES(title), year = VALUES(year)
                """,
                batch
            )
            conn.commit()
        finally:
            cur.close()
    
    # Re-fetch all film IDs into cache
    print("Loading film IDs into cache...")
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, slug FROM films")
        for fid, fslug in cur.fetchall():
            films_cache[fslug] = fid
    finally:
        cur.close()

    # 4. Insert nominations
    print("Inserting nominations...")
    nominations_data = []
    paraphraser = TextParaphraser()
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Nominations"):
        year_ceremony = int(row['year_ceremony'])
        cat_name = str(row['category']).strip()
        cat_slug = slugify(cat_name)
        film_title = str(row['film']).strip()
        year_film = int(row['year_film'])
        film_slug = slugify(f"{film_title} {year_film}")
        
        edition_id = editions_cache.get((ceremony_id, year_ceremony))
        category_id = categories_cache.get((ceremony_id, cat_slug))
        film_id = films_cache.get(film_slug)
        
        if not edition_id or not category_id:
            logging.error(f"Missing references for row {idx}: edition_id={edition_id}, category_id={category_id}")
            continue

        nominee_text = str(row['name']).strip()
        is_winner = int(bool(row['winner']))
        source_ref = f"kaggle:row:{idx}"
        
        # Paraphrase nominee text
        try:
            nominee_text = paraphraser.paraphrase(nominee_text)
        except Exception:
            pass

        nominations_data.append((
            edition_id,
            category_id,
            film_id,
            None, # person_id is set in enrichment stage
            nominee_text,
            is_winner,
            source_ref
        ))

    # Insert nominations in batches
    print("Writing nominations to database...")
    batch_size = 2000
    for i in range(0, len(nominations_data), batch_size):
        batch = nominations_data[i:i+batch_size]
        cur = conn.cursor()
        try:
            cur.executemany(
                """
                INSERT IGNORE INTO nominations (edition_id, category_id, film_id, person_id, nominee_text, is_winner, source_ref)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                batch
            )
            conn.commit()
        finally:
            cur.close()

    conn.close()
    print("Ingestion complete!")

if __name__ == "__main__":
    main()
