import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from base import WikiScraper

def run_scraper(conn, force=False):
    s = WikiScraper("korean-association-of-film-critics-awards", "Korean Association of Film Critics Awards", "South Korea", 1977)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Korean_Association_of_Film_Critics_Awards", "Film", 0),
        ("Best Director", "https://en.wikipedia.org/wiki/Korean_Association_of_Film_Critics_Awards", "Directing", 1),
        ("Best Actor", "https://en.wikipedia.org/wiki/Korean_Association_of_Film_Critics_Awards", "Acting", 2),
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
