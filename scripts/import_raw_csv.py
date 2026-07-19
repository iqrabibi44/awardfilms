import os
import sys
import glob
import pandas as pd
import mysql.connector
from tqdm import tqdm
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from lib.text_spinner import TextParaphraser

try:
    from slugify import slugify as _slugify
    def slugify(t):
        return _slugify(str(t))[:300]
except ImportError:
    import unicodedata
    def slugify(t):
        t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
        return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", t.lower())).strip("-")[:300]

def get_db():
    return mysql.connector.connect(
        host="127.0.0.1", port=3306, user="root", password="",
        database="awardfilms_db", charset="utf8mb4"
    )

def ensure_ceremony(conn, name):
    slug = slugify(name)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ceremonies (slug, name, country)
        VALUES (%s, %s, 'Global')
        ON DUPLICATE KEY UPDATE name=VALUES(name)
        """, (slug, name)
    )
    cur.execute("SELECT id FROM ceremonies WHERE slug = %s", (slug,))
    row = cur.fetchone()
    cur.close()
    return row[0]

def ensure_edition(conn, ceremony_id, year, prefix):
    ed_slug = f"{prefix}-{year}"
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO editions (ceremony_id, year, slug)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE slug = VALUES(slug)
        """, (ceremony_id, year, ed_slug)
    )
    cur.execute("SELECT id FROM editions WHERE ceremony_id = %s AND year = %s", (ceremony_id, year))
    row = cur.fetchone()
    cur.close()
    return row[0]

def ensure_category(conn, ceremony_id, cat_name):
    cat_slug = slugify(f"{ceremony_id}-{cat_name}")
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO categories (ceremony_id, slug, name, department)
        VALUES (%s, %s, %s, 'General')
        ON DUPLICATE KEY UPDATE name = VALUES(name)
        """, (ceremony_id, cat_slug, cat_name)
    )
    cur.execute("SELECT id FROM categories WHERE ceremony_id = %s AND slug = %s", (ceremony_id, cat_slug))
    row = cur.fetchone()
    cur.close()
    return row[0]

def ensure_film(conn, title, year):
    film_slug = slugify(f"{title} {year}")
    if not film_slug:
        return None
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO films (slug, title, year, country, language)
        VALUES (%s, %s, %s, 'Global', 'English')
        ON DUPLICATE KEY UPDATE title=VALUES(title)
        """, (film_slug, title, year)
    )
    cur.execute("SELECT id FROM films WHERE slug = %s", (film_slug,))
    row = cur.fetchone()
    cur.close()
    return row[0]

def parse_raw_csv_name(filename):
    basename = os.path.basename(filename).replace('.csv', '')
    if '--' in basename:
        parts = basename.split('--', 1)
        ceremony_slug = parts[0]
        category_slug = parts[1]
        ceremony_name = ceremony_slug.replace('-', ' ').title()
        category_name = category_slug.replace('-', ' ').title()
        return ceremony_name, category_name
    return basename.replace('-', ' ').title(), 'General'

def extract_year_from_text(text):
    if not isinstance(text, str):
        return None
    m = re.search(r'\b(19[2-9]\d|20[0-3]\d)\b', text)
    if m:
        return int(m.group(1))
    return None

def process_raw_csvs(conn, raw_dir, paraphraser):
    csv_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    ceremonies = {}
    editions = {}
    categories = {}
    films = {}
    
    total_inserted = 0
    cur = conn.cursor()
    
    for csv_path in csv_files:
        print(f"Loading {csv_path}...")
        df = pd.read_csv(csv_path)
        ceremony_name, category_name = parse_raw_csv_name(csv_path)
        
        if ceremony_name not in ceremonies:
            ceremonies[ceremony_name] = ensure_ceremony(conn, ceremony_name)
        c_id = ceremonies[ceremony_name]
        
        cat_key = f"{c_id}-{category_name}"
        if cat_key not in categories:
            categories[cat_key] = ensure_category(conn, c_id, category_name)
        cat_id = categories[cat_key]
        
        inserted = 0
        for _, row in tqdm(df.iterrows(), total=len(df), desc=os.path.basename(csv_path)):
            year = row.get('year')
            if pd.isna(year):
                # Try to extract year from raw_text
                year = extract_year_from_text(row.get('raw_text'))
                if not year:
                    year = extract_year_from_text(row.get('source_url'))
                    if not year:
                        continue
            
            try:
                year = int(float(year))
            except:
                continue
                
            if year < 1920 or year > 2030:
                continue
                
            film_title = str(row.get('film')).strip()
            person_name = str(row.get('person')).strip()
            
            if pd.isna(row.get('film')) or film_title == 'nan':
                film_title = person_name
            if pd.isna(row.get('person')) or person_name == 'nan':
                person_name = film_title
                
            if pd.isna(film_title) or film_title == 'nan' or not film_title:
                continue
                
            is_winner = 1 if str(row.get('is_winner', '')).lower() in ('true', '1', 'winner', 'yes') else 0
            
            ed_key = f"{c_id}-{year}"
            if ed_key not in editions:
                editions[ed_key] = ensure_edition(conn, c_id, year, slugify(ceremony_name))
            e_id = editions[ed_key]
            
            film_key = f"{film_title}-{year}"
            if film_key not in films:
                films[film_key] = ensure_film(conn, film_title, year - 1)
            f_id = films[film_key]
            
            if not f_id:
                continue
                
            spun_text = person_name
            source = str(row.get('source_url', ''))
            
            cur.execute(
                """
                INSERT IGNORE INTO nominations
                    (edition_id, category_id, film_id, nominee_text, is_winner, source_ref)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (e_id, cat_id, f_id, spun_text, is_winner, source)
            )
            inserted += 1
            
        conn.commit()
        print(f" -> Inserted {inserted} nominations.\n")
        total_inserted += inserted
        
    cur.close()
    return total_inserted

def process_oscars(conn, csv_path, paraphraser):
    if not os.path.exists(csv_path):
        return
        
    print(f"Loading Oscars from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    c_id = ensure_ceremony(conn, "Academy Awards")
    editions = {}
    categories = {}
    films = {}
    
    inserted = 0
    cur = conn.cursor()
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Oscars"):
        year = row.get('year_ceremony')
        if pd.isna(year):
            continue
        try:
            year = int(float(year))
        except:
            continue
            
        category_name = str(row.get('category')).strip()
        film_title = str(row.get('film')).strip()
        person_name = str(row.get('name')).strip()
        
        if pd.isna(row.get('film')) or film_title == 'nan':
            film_title = person_name
        if pd.isna(row.get('name')) or person_name == 'nan':
            person_name = film_title
            
        if pd.isna(film_title) or film_title == 'nan' or not film_title:
            continue
            
        is_winner = 1 if str(row.get('winner', '')).lower() in ('true', '1') else 0
        
        ed_key = f"{c_id}-{year}"
        if ed_key not in editions:
            editions[ed_key] = ensure_edition(conn, c_id, year, "oscars")
        e_id = editions[ed_key]
        
        cat_key = f"{c_id}-{category_name}"
        if cat_key not in categories:
            categories[cat_key] = ensure_category(conn, c_id, category_name)
        cat_id = categories[cat_key]
        
        film_key = f"{film_title}-{year}"
        if film_key not in films:
            films[film_key] = ensure_film(conn, film_title, year - 1)
        f_id = films[film_key]
        if not f_id:
            continue
            
        spun_text = person_name
        source = 'the_oscar_award.csv'
        
        cur.execute(
            """
            INSERT IGNORE INTO nominations
                (edition_id, category_id, film_id, nominee_text, is_winner, source_ref)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (e_id, cat_id, f_id, spun_text, is_winner, source)
        )
        inserted += 1
        
    conn.commit()
    cur.close()
    print(f" -> Inserted {inserted} Oscar nominations.\n")

def main():
    conn = get_db()
    paraphraser = TextParaphraser()
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    # Process RAW CSVs
    raw_dir = os.path.join(base_dir, "scripts", "data", "raw")
    process_raw_csvs(conn, raw_dir, paraphraser)
    
    # Process Lollywood
    lollywood_dir = os.path.join(base_dir, "lib", "data", "lollywood")
    if os.path.exists(lollywood_dir):
        process_raw_csvs(conn, lollywood_dir, paraphraser)
    
    # Process Oscars
    oscar_csv = os.path.join(base_dir, "scripts", "data", "the_oscar_award.csv")
    process_oscars(conn, oscar_csv, paraphraser)
    
    conn.close()
    print("Done importing RAW CSVs and Oscars!")

if __name__ == "__main__":
    main()
