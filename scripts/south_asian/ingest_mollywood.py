"""
scripts/south_asian/ingest_mollywood.py
Kerala State Film Awards (Mollywood)
"""
import time
import requests
from tqdm import tqdm
from shared_ingester import get_db, get_ceremony_id, upsert_edition, upsert_category, upsert_film, upsert_nomination, parse_standard_wikitable

WIKI_BASE = "https://en.wikipedia.org/wiki/"
CATEGORIES = [
    {"name": "Best Film", "slug": "kerala-best-film", "wiki": "Kerala_State_Film_Award_for_Best_Film", "dept": "Film", "is_craft": False},
    {"name": "Best Director", "slug": "kerala-director", "wiki": "Kerala_State_Film_Award_for_Best_Director", "dept": "Directing", "is_craft": False},
    {"name": "Best Actor", "slug": "kerala-actor", "wiki": "Kerala_State_Film_Award_for_Best_Actor", "dept": "Acting", "is_craft": False},
    {"name": "Best Actress", "slug": "kerala-actress", "wiki": "Kerala_State_Film_Award_for_Best_Actress", "dept": "Acting", "is_craft": False},
]

def main():
    conn = get_db()
    cid = get_ceremony_id(conn, "kerala-state-film-awards")
    total = 0
    editions = {}
    for cat in tqdm(CATEGORIES, desc="Kerala State (Mollywood)"):
        cat_id = upsert_category(conn, cid, cat["slug"], cat["name"], cat["dept"], is_craft=cat["is_craft"])
        r = requests.get(WIKI_BASE + cat["wiki"], headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200: continue
        recs = parse_standard_wikitable(r.text)
        for rec in recs:
            if rec["year"] < 1969: continue
            if rec["year"] not in editions:
                editions[rec["year"]] = upsert_edition(conn, cid, rec["year"], 1969, "kerala")
            fid = upsert_film(conn, rec["film"], rec["year"] - 1, "India", "Malayalam")
            upsert_nomination(conn, editions[rec["year"]], cat_id, fid, rec["nominee"], rec["is_winner"], "wikipedia:kerala")
            total += 1
        time.sleep(0.5)

    conn.close()
    print(f"Mollywood complete: {total} records.")

if __name__ == "__main__":
    main()
