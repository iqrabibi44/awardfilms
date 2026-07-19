"""
scripts/south_asian/ingest_lux_style.py
Lux Style Awards ingestion. Note: Some years may have no ceremony due to COVID.
"""
import time
import requests
from tqdm import tqdm
from shared_ingester import get_db, get_ceremony_id, upsert_edition, upsert_category, upsert_film, upsert_nomination, parse_standard_wikitable

WIKI_BASE = "https://en.wikipedia.org/wiki/"
CATEGORIES = [
    {"name": "Best Film", "slug": "lsa-best-film", "wiki": "Lux_Style_Award_for_Best_Film", "dept": "Film"},
    {"name": "Best Director", "slug": "lsa-director", "wiki": "Lux_Style_Award_for_Best_Film_Director", "dept": "Directing"},
    {"name": "Best Actor", "slug": "lsa-actor", "wiki": "Lux_Style_Award_for_Best_Film_Actor", "dept": "Acting"},
    {"name": "Best Actress", "slug": "lsa-actress", "wiki": "Lux_Style_Award_for_Best_Film_Actress", "dept": "Acting"},
]

def main():
    conn = get_db()
    cid = get_ceremony_id(conn, "lux-style-awards")
    total = 0
    editions = {}
    for cat in tqdm(CATEGORIES, desc="Lux Style Awards"):
        cat_id = upsert_category(conn, cid, cat["slug"], cat["name"], cat["dept"])
        r = requests.get(WIKI_BASE + cat["wiki"], headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200: continue
        recs = parse_standard_wikitable(r.text)
        for rec in recs:
            if rec["year"] < 2002: continue
            if rec["year"] not in editions:
                editions[rec["year"]] = upsert_edition(conn, cid, rec["year"], 2002, "lsa")
            fid = upsert_film(conn, rec["film"], rec["year"] - 1, "Pakistan", "Urdu")
            upsert_nomination(conn, editions[rec["year"]], cat_id, fid, rec["nominee"], rec["is_winner"], "wikipedia:luxstyle")
            total += 1
        time.sleep(0.5)

    conn.close()
    print(f"Lux Style Awards complete: {total} records.")

if __name__ == "__main__":
    main()
