"""
scripts/south_asian/enrich_lollywood_tmdb.py
Enriches Lollywood/Pakistani films from TMDb.
"""
import os
import sys
import time
import requests
import psycopg2
from dotenv import load_dotenv
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")

def get_db():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def search_tmdb(title, year):
    url = f"https://api.themoviedb.org/3/search/movie"
    
    # Try with region PK and lang ur first
    params = {"api_key": TMDB_API_KEY, "query": title, "region": "PK"}
    if year: params["primary_release_year"] = year
    
    try:
        r = requests.get(url, params=params, timeout=10)
        res = r.json().get("results", [])
        if res: return res[0]
        
        # Fallback to general search (many PK films use English titles)
        del params["region"]
        r = requests.get(url, params=params, timeout=10)
        res = r.json().get("results", [])
        if res: return res[0]
            
        return None
    except Exception:
        return None

def main():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT f.id, f.title, f.year
            FROM films f
            JOIN nominations n ON n.film_id = f.id
            JOIN editions e ON n.edition_id = e.id
            JOIN ceremonies c ON e.ceremony_id = c.id
            WHERE c.slug IN ('lux-style-awards', 'ary-film-awards', 'hum-awards', 'pisa', 'nigar-awards')
              AND f.tmdb_id IS NULL
            """
        )
        films = cur.fetchall()
        
    print(f"Found {len(films)} Lollywood films missing tmdb_id.")
    
    updates, not_found = 0, 0
    unmatched_file = open(os.path.join(LOG_DIR, "lollywood_unmatched.log"), "w")
    
    with conn.cursor() as cur:
        for fid, title, year in tqdm(films, desc="TMDb Search"):
            res = search_tmdb(title, year)
            if res:
                tmdb_id = res["id"]
                poster_path = res.get("poster_path")
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                cur.execute(
                    "UPDATE films SET tmdb_id = %s, poster_url = %s, plot_summary = %s WHERE id = %s",
                    (tmdb_id, poster_url, res.get("overview"), fid)
                )
                updates += 1
            else:
                cur.execute("UPDATE films SET tmdb_id = -1 WHERE id = %s", (fid,))
                unmatched_file.write(f"UNMATCHED: {title} ({year})\n")
                not_found += 1
            conn.commit()
            time.sleep(0.26)
            
    unmatched_file.close()
    conn.close()
    print(f"TMDb Lollywood enrichment: {updates} matched, {not_found} missing (logged).")

if __name__ == "__main__":
    main()
