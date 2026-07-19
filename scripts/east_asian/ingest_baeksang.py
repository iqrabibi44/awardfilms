"""
scripts/east_asian/ingest_baeksang.py
"""
import time
import requests
from tqdm import tqdm
from shared_ingester import get_db, get_ceremony_id, upsert_edition, upsert_category, upsert_film, upsert_nomination, parse_standard_wikitable

WIKI_BASE = "https://en.wikipedia.org/wiki/"
CATEGORIES = [
    {"name": "Best Film",     "slug": "baeksang-best-film",     "wiki": "Baeksang_Arts_Award_for_Best_Film",     "dept": "Film"},
    {"name": "Best Director", "slug": "baeksang-best-director", "wiki": "Baeksang_Arts_Award_for_Best_Director_-_Film", "dept": "Directing"},
    {"name": "Best Actor",    "slug": "baeksang-best-actor",    "wiki": "Baeksang_Arts_Award_for_Best_Actor_-_Film",    "dept": "Acting"},
    {"name": "Best Actress",  "slug": "baeksang-best-actress",  "wiki": "Baeksang_Arts_Award_for_Best_Actress_-_Film",  "dept": "Acting"},
]

def main():
    conn = get_db()
    cid = get_ceremony_id(conn, "baeksang")
    
    total = 0
    editions, categories = {}, {}
    for cat in tqdm(CATEGORIES, desc="Baeksang"):
        cat_id = upsert_category(conn, cid, cat["slug"], cat["name"], cat["dept"])
        
        r = requests.get(WIKI_BASE + cat["wiki"], headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200: continue
        
        recs = parse_standard_wikitable(r.text)
        for rec in recs:
            if rec["year"] < 1965: continue
            if rec["year"] not in editions:
                editions[rec["year"]] = upsert_edition(conn, cid, rec["year"], 1965, "baeksang")
            
            fid = upsert_film(conn, rec["film"], rec["year"] - 1, "South Korea", "Korean")
            src = f"wikipedia:baeksang:{rec['year']}"
            upsert_nomination(conn, editions[rec["year"]], cat_id, fid, rec["nominee"], rec["is_winner"], src)
            total += 1
        time.sleep(0.5)

    conn.close()
    print(f"Baeksang complete: {total} records.")

if __name__ == "__main__":
    main()
