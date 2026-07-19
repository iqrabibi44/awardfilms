import os
import sys
import re
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Use custom slugify if python-slugify isn't loaded
try:
    from slugify import slugify
except ImportError:
    def slugify(t):
        import unicodedata
        t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
        return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", t.lower())).strip("-")

# Load environment variables
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env.local")) # Try .env.local first
if not os.environ.get("DATABASE_URL"):
    load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, "scripts", ".env")) # Fallback

DATABASE_URL = os.environ.get("DATABASE_URL")
CEREMONY_SLUG = "amaa"

# Mapping categories to database departments & is_craft flags
DEPT_MAP = {
    "Best Film": ("Film", False),
    "Best Director": ("Directing", False),
    "Best Actor in a Leading Role": ("Acting", False),
    "Best Actress in a Leading Role": ("Acting", False),
    "Best Actor in a Supporting Role": ("Acting", False),
    "Best Actress in a Supporting Role": ("Acting", False),
    "Best Animation": ("Film", False),
    "Best Cinematography": ("Cinematography", True),
    "Best Costume Design": ("Costume Design", True),
    "Best Diaspora Documentary": ("Documentary", False),
    "Best Diaspora Feature": ("Film", False),
    "Best Documentary": ("Documentary", False),
    "Best Editing": ("Editing", True),
    "Best Film by an African Living Abroad": ("Film", False),
    "Best Film in an African Language": ("Film", False),
    "Best Makeup": ("Other", True),
    "Best Nigerian Film": ("Film", False),
    "Best Production Design": ("Art Direction", True),
    "Best Screenplay": ("Writing", False),
    "Best Short Film": ("Short Film", False),
    "Best Sound": ("Sound", True),
    "Best Soundtrack": ("Music", True),
    "Best Visual Effects": ("Visual Effects", True),
    "Most Promising Actor": ("Acting", False)
}

def get_db_connection():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set in environment.")
        sys.exit(1)
    return psycopg2.connect(DATABASE_URL)

def main():
    csv_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(csv_dir, "amaa_awards.csv")
    
    if not os.path.exists(csv_path):
        print(f"ERROR: Scraped CSV file not found at: {csv_path}")
        sys.exit(1)
        
    print(f"[*] Reading scraped data from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. Verify and retrieve Ceremony ID
            cur.execute("SELECT id FROM ceremonies WHERE slug = %s", (CEREMONY_SLUG,))
            ceremony_row = cur.fetchone()
            if not ceremony_row:
                # Let's insert the ceremony if it doesn't exist
                cur.execute(
                    """
                    INSERT INTO ceremonies (name, slug, type, country)
                    VALUES ('African Movie Academy Awards', 'amaa', 'Film', 'Nigeria')
                    RETURNING id
                    """
                )
                ceremony_id = cur.fetchone()[0]
                print(f"[+] Created ceremony 'African Movie Academy Awards' with ID: {ceremony_id}")
            else:
                ceremony_id = ceremony_row[0]
                print(f"[*] Found ceremony 'African Movie Academy Awards' with ID: {ceremony_id}")
                
            # 2. Clean old AMAA data (Editions and Categories). Cascade delete handles Nominations.
            print("[*] Cleaning existing AMAA editions and categories to ensure a fresh import...")
            cur.execute("DELETE FROM editions WHERE ceremony_id = %s", (ceremony_id,))
            cur.execute("DELETE FROM categories WHERE ceremony_id = %s", (ceremony_id,))
            conn.commit()
            print("[+] Previous AMAA data cleared successfully.")
            
            # Caches to avoid duplicate DB operations
            editions_cache = {} # year -> edition_id
            categories_cache = {} # category_name -> category_id
            films_cache = {} # (title, year) -> film_id
            
            inserted_nominations_count = 0
            
            # 3. Iterate through scraped records
            print("[*] Ingesting scraped records into database...")
            for idx, row in df.iterrows():
                year = int(row["year"])
                category = row["category"]
                nominee = row["nominee"]
                film_title = row["film"]
                winner_val = bool(row["winner"])
                source_url = row["source_url"]
                
                # Check / Upsert Category
                if category not in categories_cache:
                    cat_slug = f"amaa-{slugify(category)}"
                    dept, is_craft = DEPT_MAP.get(category, ("Other", False))
                    cur.execute(
                        """
                        INSERT INTO categories (ceremony_id, slug, name, department, is_craft)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (ceremony_id, slug) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id
                        """,
                        (ceremony_id, cat_slug, category, dept, is_craft)
                    )
                    categories_cache[category] = cur.fetchone()[0]
                    
                category_id = categories_cache[category]
                
                # Check / Upsert Edition
                if year not in editions_cache:
                    edition_num = year - 2004
                    edition_slug = f"amaa-{year}"
                    cur.execute(
                        """
                        INSERT INTO editions (ceremony_id, edition_number, year, slug)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (ceremony_id, year) DO UPDATE SET slug = EXCLUDED.slug
                        RETURNING id
                        """,
                        (ceremony_id, edition_num, year, edition_slug)
                    )
                    editions_cache[year] = cur.fetchone()[0]
                    
                edition_id = editions_cache[year]
                
                # Check / Upsert Film
                film_id = None
                if film_title and str(film_title).lower() != "nan" and str(film_title).lower() != "n/a":
                    film_key = (film_title, year)
                    if film_key not in films_cache:
                        film_slug = slugify(f"{film_title} {year}")
                        if film_slug:
                            cur.execute(
                                """
                                INSERT INTO films (slug, title, year, country, language)
                                VALUES (%s, %s, %s, 'Nigeria', 'English')
                                ON CONFLICT (slug) DO UPDATE SET title = EXCLUDED.title
                                RETURNING id
                                """,
                                (film_slug, film_title, year)
                            )
                            films_cache[film_key] = cur.fetchone()[0]
                    film_id = films_cache.get(film_key, None)
                    
                # Insert Nomination
                nominee_str = nominee if (nominee and str(nominee).lower() != "nan") else film_title
                if not nominee_str:
                    nominee_str = "Unknown Nominee"
                    
                cur.execute(
                    """
                    INSERT INTO nominations (edition_id, category_id, film_id, person_id, nominee_text, is_winner, source_ref)
                    VALUES (%s, %s, %s, NULL, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (edition_id, category_id, film_id, nominee_str, winner_val, source_url)
                )
                inserted_nominations_count += 1
                
            conn.commit()
            print(f"[+] Ingestion complete! Successfully loaded {inserted_nominations_count} nominations into the database.")
            
    except Exception as e:
        conn.rollback()
        print(f"[-] ERROR: Failed database transaction: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
