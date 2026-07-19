"""
scripts/south_asian/ingest_ary_hum.py
ARY Film Awards and Hum Awards.
"""
import time
import requests
from tqdm import tqdm
from shared_ingester import get_db, get_ceremony_id, upsert_edition, upsert_category, upsert_film, upsert_nomination, parse_standard_wikitable

WIKI_BASE = "https://en.wikipedia.org/wiki/"

ARY_CATS = [
    {"name": "Best Film", "slug": "ary-best-film", "wiki": "ARY_Film_Award_for_Best_Film", "dept": "Film"},
    {"name": "Best Director", "slug": "ary-director", "wiki": "ARY_Film_Award_for_Best_Director", "dept": "Directing"},
    {"name": "Best Actor", "slug": "ary-actor", "wiki": "ARY_Film_Award_for_Best_Actor", "dept": "Acting"},
]

HUM_CATS = [
    {"name": "Best Film", "slug": "hum-best-film", "wiki": "Hum_Award_for_Best_Film", "dept": "Film"},
    {"name": "Best Actor Film", "slug": "hum-actor-film", "wiki": "Hum_Award_for_Best_Actor_in_a_Film", "dept": "Acting"},
]

def ingest_ceremony(conn, slug, cats, base_year, desc_name):
    cid = get_ceremony_id(conn, slug)
    total = 0
    editions = {}
    for cat in tqdm(cats, desc=desc_name):
        cat_id = upsert_category(conn, cid, cat["slug"], cat["name"], cat["dept"])
        r = requests.get(WIKI_BASE + cat["wiki"], headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200: continue
        recs = parse_standard_wikitable(r.text)
        for rec in recs:
            if rec["year"] < base_year: continue
            if rec["year"] not in editions:
                editions[rec["year"]] = upsert_edition(conn, cid, rec["year"], base_year, slug)
            fid = upsert_film(conn, rec["film"], rec["year"] - 1, "Pakistan", "Urdu")
            upsert_nomination(conn, editions[rec["year"]], cat_id, fid, rec["nominee"], rec["is_winner"], f"wikipedia:{slug}")
            total += 1
        time.sleep(0.5)
    return total

def main():
    conn = get_db()
    t1 = ingest_ceremony(conn, "ary-film-awards", ARY_CATS, 2014, "ARY")
    t2 = ingest_ceremony(conn, "hum-awards", HUM_CATS, 2013, "Hum")
    conn.close()
    print(f"ARY & Hum complete: {t1+t2} records.")

if __name__ == "__main__":
    main()
