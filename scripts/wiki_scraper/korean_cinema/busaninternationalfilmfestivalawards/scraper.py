import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from base import WikiScraper

def run_scraper(conn, force=False):
    s = WikiScraper("busan-international-film-festival-awards", "Busan International Film Festival Awards", "South Korea", 1996)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("General", "https://en.wikipedia.org/wiki/Busan_International_Film_Festival", "Film", 0),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept, idx in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="South Korea", film_language="Korean",
            table_index=idx, force_rescrape=force
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    run_scraper(conn, force=True)
    conn.close()
