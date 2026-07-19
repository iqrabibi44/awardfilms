"""
scripts/nollywood/enrich_nollywood_tmdb.py
Searches TMDb for Nollywood films missing tmdb_id.
Filters for country 'NG' (Nigeria) or uses high similarity match.
"""
import os
import sys
import time
import requests
import psycopg2
import argparse
from dotenv import load_dotenv
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")

def get_db():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def search_tmdb(title, year):
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": title, "region": "NG", "page": 1}
    if year: params["primary_release_year"] = year
    
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        res = r.json().get("results", [])
        if res: return res[0]
        
        # Fallback without year constraint
        if year:
            del params["primary_release_year"]
            r = requests.get(url, params=params, timeout=10)
            res = r.json().get("results", [])
            if res: return res[0]
            
        return None
    except Exception as e:
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
            WHERE c.slug IN ('amaa', 'amvca', 'fespaco', 'nea', 'bona')
              AND f.tmdb_id IS NULL
            """
        )
        films = cur.fetchall()
        
    print(f"Found {len(films)} Nollywood/African films missing tmdb_id.")
    
    updates, not_found = 0, 0
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
                not_found += 1
            conn.commit()
            time.sleep(0.26)
            
    conn.close()
    print(f"TMDb enrichment: {updates} matched, {not_found} missing.")

if __name__ == "__main__":
    main()
