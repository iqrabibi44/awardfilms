"""
scripts/east_asian/ingest_japan_academy.py
"""
import time
import requests
from tqdm import tqdm
from shared_ingester import get_db, get_ceremony_id, upsert_edition, upsert_category, upsert_film, upsert_nomination, parse_standard_wikitable

WIKI_BASE = "https://en.wikipedia.org/wiki/"
CATEGORIES = [
    {"name": "Outstanding Film", "slug": "japan-academy-best-film", "wiki": "Japan_Academy_Film_Prize_for_Outstanding_Film", "dept": "Film"},
    {"name": "Best Director",    "slug": "japan-academy-director",  "wiki": "Japan_Academy_Film_Prize_for_Director_of_the_Year", "dept": "Directing"},
    {"name": "Best Actor",       "slug": "japan-academy-actor",     "wiki": "Japan_Academy_Film_Prize_for_Outstanding_Performance_by_an_Actor_in_a_Leading_Role", "dept": "Acting"},
    {"name": "Best Actress",     "slug": "japan-academy-actress",   "wiki": "Japan_Academy_Film_Prize_for_Outstanding_Performance_by_an_Actress_in_a_Leading_Role", "dept": "Acting"},
]

def main():
    conn = get_db()
    cid = get_ceremony_id(conn, "japan-academy-film-prize")
    total = 0
    editions = {}
    for cat in tqdm(CATEGORIES, desc="Japan Academy"):
        cat_id = upsert_category(conn, cid, cat["slug"], cat["name"], cat["dept"])
        r = requests.get(WIKI_BASE + cat["wiki"], headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200: continue
        recs = parse_standard_wikitable(r.text)
        for rec in recs:
            if rec["year"] < 1978: continue
            if rec["year"] not in editions:
                editions[rec["year"]] = upsert_edition(conn, cid, rec["year"], 1978, "japan-academy")
            fid = upsert_film(conn, rec["film"], rec["year"] - 1, "Japan", "Japanese")
            upsert_nomination(conn, editions[rec["year"]], cat_id, fid, rec["nominee"], rec["is_winner"], "wikipedia:japanacademy")
            total += 1
        time.sleep(0.5)

    conn.close()
    print(f"Japan Academy complete: {total} records.")

if __name__ == "__main__":
    main()
