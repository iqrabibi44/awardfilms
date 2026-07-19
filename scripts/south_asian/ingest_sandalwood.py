"""
scripts/south_asian/ingest_sandalwood.py
Karnataka State Film Awards (Sandalwood)
"""
import time
import requests
from tqdm import tqdm
from shared_ingester import get_db, get_ceremony_id, upsert_edition, upsert_category, upsert_film, upsert_nomination, parse_standard_wikitable

WIKI_BASE = "https://en.wikipedia.org/wiki/"
CATEGORIES = [
    {"name": "Best Direction", "slug": "karnataka-director", "wiki": "Karnataka_State_Film_Award_for_Best_Direction", "dept": "Directing"},
    {"name": "Best Actor", "slug": "karnataka-actor", "wiki": "Karnataka_State_Film_Award_for_Best_Actor", "dept": "Acting"},
]

def main():
    conn = get_db()
    cid = get_ceremony_id(conn, "karnataka-state-film-awards")
    total = 0
    editions = {}
    for cat in tqdm(CATEGORIES, desc="Karnataka State (Sandalwood)"):
        cat_id = upsert_category(conn, cid, cat["slug"], cat["name"], cat["dept"])
        r = requests.get(WIKI_BASE + cat["wiki"], headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200: continue
        recs = parse_standard_wikitable(r.text)
        for rec in recs:
            if rec["year"] < 1967: continue
            if rec["year"] not in editions:
                editions[rec["year"]] = upsert_edition(conn, cid, rec["year"], 1967, "karnataka")
            fid = upsert_film(conn, rec["film"], rec["year"] - 1, "India", "Kannada")
            upsert_nomination(conn, editions[rec["year"]], cat_id, fid, rec["nominee"], rec["is_winner"], "wikipedia:karnataka")
            total += 1
        time.sleep(0.5)

    conn.close()
    print(f"Sandalwood complete: {total} records.")

if __name__ == "__main__":
    main()
