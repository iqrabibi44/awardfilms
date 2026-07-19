"""
scripts/bollywood/enrich_bollywood_persons.py
Searches TMDb for Bollywood persons (actors, directors, etc.) missing person_id.
Upserts into persons table and updates nominations.
"""
import os
import sys
import time
import argparse
import requests
import psycopg2
from dotenv import load_dotenv
from tqdm import tqdm

try:
    from slugify import slugify
except ImportError:
    def slugify(t):
        import unicodedata
        import re
        t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
        return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", t.lower())).strip("-")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")

def get_db():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(url)

def search_tmdb_person(name):
    url = f"https://api.themoviedb.org/3/search/person"
    params = {
        "api_key": TMDB_API_KEY,
        "query": name,
        "language": "en-US",
        "page": 1,
        "include_adult": "false"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        if results:
            return results[0]
        return None
    except Exception as e:
        print(f"TMDb error for person '{name}': {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=300)
    args = parser.parse_args()

    conn = get_db()
    with conn.cursor() as cur:
        # Get unique nominee_text for Bollywood nominations lacking person_id
        cur.execute(
            """
            SELECT DISTINCT n.nominee_text
            FROM nominations n
            JOIN editions e ON n.edition_id = e.id
            JOIN ceremonies c ON e.ceremony_id = c.id
            WHERE c.slug IN ('filmfare', 'national-film-awards-india', 'iifa', 'screen-awards', 'zee-cine-awards')
              AND n.person_id IS NULL
              AND n.nominee_text IS NOT NULL
              AND n.nominee_text != ''
            LIMIT %s
            """,
            (args.limit,)
        )
        nominees = [r[0] for r in cur.fetchall()]

    print(f"Found {len(nominees)} distinct person names missing person_id.")
    
    new_persons = 0
    updated_noms = 0

    for name in tqdm(nominees, desc="Enriching Persons from TMDb"):
        res = search_tmdb_person(name)
        
        person_id = None
        with conn.cursor() as cur:
            if res:
                tmdb_id = res["id"]
                person_name = res["name"]
                person_slug = slugify(person_name)
                profile_path = res.get("profile_path")
                photo_url = f"https://image.tmdb.org/t/p/w500{profile_path}" if profile_path else None
                dept = res.get("known_for_department")
                
                # Upsert person
                cur.execute(
                    """
                    INSERT INTO persons (slug, name, tmdb_id, photo_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (slug) DO UPDATE SET
                        tmdb_id = EXCLUDED.tmdb_id,
                        photo_url = COALESCE(persons.photo_url, EXCLUDED.photo_url)
                    RETURNING id
                    """,
                    (person_slug, person_name, tmdb_id, photo_url)
                )
                person_id = cur.fetchone()[0]
                new_persons += 1
            else:
                # Create a placeholder person without TMDb info
                person_slug = slugify(name)
                cur.execute(
                    """
                    INSERT INTO persons (slug, name)
                    VALUES (%s, %s)
                    ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                    """,
                    (person_slug, name)
                )
                person_id = cur.fetchone()[0]

            # Update nominations for this name
            cur.execute(
                """
                UPDATE nominations
                SET person_id = %s
                WHERE nominee_text = %s
                AND person_id IS NULL
                """,
                (person_id, name)
            )
            updated_noms += cur.rowcount
            conn.commit()
            
        time.sleep(0.26)  # TMDb rate limit

    conn.close()
    print(f"Person enrichment complete: {new_persons} TMDb matches, {updated_noms} nominations updated.")

if __name__ == "__main__":
    main()
