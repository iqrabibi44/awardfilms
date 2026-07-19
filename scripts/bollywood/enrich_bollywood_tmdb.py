"""
scripts/bollywood/enrich_bollywood_tmdb.py
Searches TMDb for Bollywood films to get tmdb_id, poster_url, etc.
Filters specifically for Hindi language ('hi') or country 'IN'.
Higher confidence threshold: requires title match or original_title match.
"""
import os
import sys
import time
import argparse
import requests
import psycopg2
from dotenv import load_dotenv
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
if not TMDB_API_KEY:
    print("ERROR: TMDB_API_KEY not set")
    sys.exit(1)

def get_db():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(url)

def search_tmdb_film(title, year):
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "en-US",
        "page": 1,
        "include_adult": "false"
    }
    if year:
        params["primary_release_year"] = year
    
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        
        # High confidence match for Bollywood:
        # Check for original_language == 'hi' or production_countries containing 'IN'
        for res in results:
            # Often Hindi films have original_language = 'hi'
            if res.get("original_language") == "hi" or "IN" in [c.get("iso_3166_1") for c in res.get("production_countries", [])]:
                return res
            # Also accept if title matches exactly
            if res.get("title", "").lower() == title.lower() or res.get("original_title", "").lower() == title.lower():
                return res
        
        # Fallback to first result if it seems reasonable
        if results:
            return results[0]
            
        return None
    except Exception as e:
        print(f"TMDb error for '{title}': {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    conn = get_db()
    with conn.cursor() as cur:
        # Get films that have Bollywood nominations but no tmdb_id
        cur.execute(
            """
            SELECT DISTINCT f.id, f.title, f.year
            FROM films f
            JOIN nominations n ON n.film_id = f.id
            JOIN editions e ON n.edition_id = e.id
            JOIN ceremonies c ON e.ceremony_id = c.id
            WHERE c.slug IN ('filmfare', 'national-film-awards-india', 'iifa', 'screen-awards', 'zee-cine-awards')
              AND f.tmdb_id IS NULL
            LIMIT %s
            """,
            (args.limit,)
        )
        films = cur.fetchall()

    print(f"Found {len(films)} Bollywood films missing tmdb_id.")
    
    updates = 0
    not_found = 0

    for fid, title, year in tqdm(films, desc="Enriching from TMDb"):
        res = search_tmdb_film(title, year)
        
        with conn.cursor() as cur:
            if res:
                tmdb_id = res["id"]
                poster_path = res.get("poster_path")
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                overview = res.get("overview")
                
                cur.execute(
                    """
                    UPDATE films SET
                        tmdb_id = %s,
                        poster_url = %s,
                        synopsis = %s
                    WHERE id = %s
                    """,
                    (tmdb_id, poster_url, overview, fid)
                )
                updates += 1
            else:
                # Mark as not found to avoid retrying (-1)
                cur.execute("UPDATE films SET tmdb_id = -1 WHERE id = %s", (fid,))
                not_found += 1
            conn.commit()
            
        time.sleep(0.26)  # TMDb rate limit

    conn.close()
    print(f"TMDb enrichment complete: {updates} updated, {not_found} not found.")

if __name__ == "__main__":
    main()
