"""
scripts/east_asian/ingest_golden_horse.py
"""
import time
import requests
from tqdm import tqdm
from shared_ingester import get_db, get_ceremony_id, upsert_edition, upsert_category, upsert_film, upsert_nomination, parse_standard_wikitable

WIKI_BASE = "https://en.wikipedia.org/wiki/"
CATEGORIES = [
    {"name": "Best Feature Film", "slug": "golden-horse-best-film", "wiki": "Golden_Horse_Award_for_Best_Feature_Film", "dept": "Film"},
    {"name": "Best Director",     "slug": "golden-horse-director",  "wiki": "Golden_Horse_Award_for_Best_Director", "dept": "Directing"},
    {"name": "Best Actor",        "slug": "golden-horse-actor",     "wiki": "Golden_Horse_Award_for_Best_Leading_Actor", "dept": "Acting"},
    {"name": "Best Actress",      "slug": "golden-horse-actress",   "wiki": "Golden_Horse_Award_for_Best_Leading_Actress", "dept": "Acting"},
]

def main():
    conn = get_db()
    cid = get_ceremony_id(conn, "golden-horse")
    total = 0
    editions = {}
    for cat in tqdm(CATEGORIES, desc="Golden Horse"):
        cat_id = upsert_category(conn, cid, cat["slug"], cat["name"], cat["dept"])
        r = requests.get(WIKI_BASE + cat["wiki"], headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200: continue
        recs = parse_standard_wikitable(r.text)
        for rec in recs:
            if rec["year"] < 1962: continue
            if rec["year"] not in editions:
                editions[rec["year"]] = upsert_edition(conn, cid, rec["year"], 1962, "golden-horse")
            # Set country broadly to Taiwan/China, language to Chinese (Mandarin)
            fid = upsert_film(conn, rec["film"], rec["year"] - 1, "Taiwan", "Chinese")
            upsert_nomination(conn, editions[rec["year"]], cat_id, fid, rec["nominee"], rec["is_winner"], "wikipedia:goldenhorse")
            total += 1
        time.sleep(0.5)

    conn.close()
    print(f"Golden Horse complete: {total} records.")

if __name__ == "__main__":
    main()
