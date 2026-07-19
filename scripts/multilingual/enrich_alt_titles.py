"""
scripts/multilingual/enrich_alt_titles.py
Fetches alternate titles for films from TMDb and upserts into the DB.
"""
import os
import sys
import time
import requests
import argparse
import psycopg2
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

TMDB_BEARER = os.environ.get("TMDB_BEARER_TOKEN")
DB_URL = os.environ.get("DATABASE_URL")

HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {TMDB_BEARER}"
}

# Map TMDb country code to Language Code and Script
# Note: 'title_type' will be set to 'translated' or 'original' based on needs, defaulting to 'original' for simplicity.
COUNTRY_LANG_MAP = {
    'IN': ('hi', 'Devanagari'),  # Hindi
    'KR': ('ko', 'Hangul'),      # Korean
    'PK': ('ur', 'Arabic'),      # Urdu
    'NG': ('yo', 'Latin'),       # Yoruba best effort
    'JP': ('ja', 'Kanji/Kana'),  # Japanese
    'FR': ('fr', 'Latin'),       # French
    'ES': ('es', 'Latin'),       # Spanish
    'DE': ('de', 'Latin'),       # German
    'IT': ('it', 'Latin'),       # Italian
    'BR': ('pt', 'Latin'),       # Portuguese
}

def get_db():
    if not DB_URL:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)
    return psycopg2.connect(DB_URL)

def enrich_films(conn, limit=None):
    with conn.cursor() as cur:
        # Get films with a TMDB ID
        cur.execute("SELECT id, title, tmdb_id FROM films WHERE tmdb_id IS NOT NULL AND tmdb_id > 0")
        films = cur.fetchall()
        
        if limit:
            films = films[:limit]
            
        print(f"Found {len(films)} films to enrich.")
        
        upsert_query = """
            INSERT INTO film_alternate_titles (film_id, title, language_code, script, title_type)
            VALUES (%(film_id)s, %(title)s, %(language_code)s, %(script)s, %(title_type)s)
            ON CONFLICT (film_id, language_code, title_type) DO UPDATE SET
                title = EXCLUDED.title,
                script = EXCLUDED.script
        """
        
        success_count = 0
        for f_id, f_title, tmdb_id in films:
            url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/alternative_titles"
            try:
                res = requests.get(url, headers=HEADERS, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    titles = data.get('titles', [])
                    for t in titles:
                        iso_code = t.get('iso_3166_1')
                        alt_title = t.get('title')
                        
                        if iso_code in COUNTRY_LANG_MAP and alt_title:
                            lang, script = COUNTRY_LANG_MAP[iso_code]
                            
                            # Do not add if it's the exact same as the English DB title
                            if alt_title.lower() == f_title.lower():
                                continue
                                
                            cur.execute(upsert_query, {
                                'film_id': f_id,
                                'title': alt_title,
                                'language_code': lang,
                                'script': script,
                                'title_type': 'original'
                            })
                    conn.commit()
                    success_count += 1
                else:
                    print(f"Error for TMDB {tmdb_id} ({f_title}): {res.status_code}")
            except Exception as e:
                print(f"Exception for TMDB {tmdb_id}: {e}")
                
            # Rate limit
            time.sleep(0.26)
            
        print(f"Enrichment complete. Processed {success_count}/{len(films)} films successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Limit number of films to process")
    args = parser.parse_args()
    
    if not TMDB_BEARER:
        print("ERROR: TMDB_BEARER_TOKEN not set in .env")
        sys.exit(1)
        
    conn = get_db()
    enrich_films(conn, args.limit)
    conn.close()
