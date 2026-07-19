"""
scripts/east_asian/ingest_hkfa.py
"""
import time
import requests
from tqdm import tqdm
from shared_ingester import get_db, get_ceremony_id, upsert_edition, upsert_category, upsert_film, upsert_nomination, parse_standard_wikitable

WIKI_BASE = "https://en.wikipedia.org/wiki/"
CATEGORIES = [
    {"name": "Best Film",     "slug": "hkfa-best-film",     "wiki": "Hong_Kong_Film_Award_for_Best_Film",     "dept": "Film"},
    {"name": "Best Director", "slug": "hkfa-director",      "wiki": "Hong_Kong_Film_Award_for_Best_Director", "dept": "Directing"},
    {"name": "Best Actor",    "slug": "hkfa-actor",         "wiki": "Hong_Kong_Film_Award_for_Best_Actor",    "dept": "Acting"},
    {"name": "Best Actress",  "slug": "hkfa-actress",       "wiki": "Hong_Kong_Film_Award_for_Best_Actress",  "dept": "Acting"},
]

def main():
    conn = get_db()
    cid = get_ceremony_id(conn, "hkfa")
    total = 0
    editions = {}
    for cat in tqdm(CATEGORIES, desc="HKFA"):
        cat_id = upsert_category(conn, cid, cat["slug"], cat["name"], cat["dept"])
        r = requests.get(WIKI_BASE + cat["wiki"], headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200: continue
        recs = parse_standard_wikitable(r.text)
        for rec in recs:
            if rec["year"] < 1982: continue
            if rec["year"] not in editions:
                editions[rec["year"]] = upsert_edition(conn, cid, rec["year"], 1982, "hkfa")
            fid = upsert_film(conn, rec["film"], rec["year"] - 1, "Hong Kong", "Cantonese")
            upsert_nomination(conn, editions[rec["year"]], cat_id, fid, rec["nominee"], rec["is_winner"], "wikipedia:hkfa")
            total += 1
        time.sleep(0.5)

    conn.close()
    print(f"HKFA complete: {total} records.")

if __name__ == "__main__":
    main()
