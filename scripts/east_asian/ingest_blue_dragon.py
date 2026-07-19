"""
scripts/east_asian/ingest_blue_dragon.py
"""
import time
import requests
from tqdm import tqdm
from shared_ingester import get_db, get_ceremony_id, upsert_edition, upsert_category, upsert_film, upsert_nomination, parse_standard_wikitable

WIKI_BASE = "https://en.wikipedia.org/wiki/"
CATEGORIES = [
    {"name": "Best Film",     "slug": "bluedragon-best-film",     "wiki": "Blue_Dragon_Film_Award_for_Best_Film",     "dept": "Film"},
    {"name": "Best Director", "slug": "bluedragon-best-director", "wiki": "Blue_Dragon_Film_Award_for_Best_Director", "dept": "Directing"},
    {"name": "Best Actor",    "slug": "bluedragon-best-actor",    "wiki": "Blue_Dragon_Film_Award_for_Best_Actor",    "dept": "Acting"},
    {"name": "Best Actress",  "slug": "bluedragon-best-actress",  "wiki": "Blue_Dragon_Film_Award_for_Best_Actress",  "dept": "Acting"},
]

def main():
    conn = get_db()
    cid = get_ceremony_id(conn, "blue-dragon")
    total = 0
    editions = {}
    for cat in tqdm(CATEGORIES, desc="Blue Dragon"):
        cat_id = upsert_category(conn, cid, cat["slug"], cat["name"], cat["dept"])
        r = requests.get(WIKI_BASE + cat["wiki"], headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200: continue
        recs = parse_standard_wikitable(r.text)
        for rec in recs:
            if rec["year"] < 1963: continue
            if rec["year"] not in editions:
                editions[rec["year"]] = upsert_edition(conn, cid, rec["year"], 1963, "blue-dragon")
            fid = upsert_film(conn, rec["film"], rec["year"] - 1, "South Korea", "Korean")
            upsert_nomination(conn, editions[rec["year"]], cat_id, fid, rec["nominee"], rec["is_winner"], "wikipedia:bluedragon")
            total += 1
        time.sleep(0.5)

    conn.close()
    print(f"Blue Dragon complete: {total} records.")

if __name__ == "__main__":
    main()
