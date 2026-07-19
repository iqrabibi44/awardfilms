import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from base import WikiScraper

def run_scraper(conn, force=False):
    s = WikiScraper("blue-dragon-film-awards", "Blue Dragon Film Awards", "South Korea", 1963)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Blue_Dragon_Film_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Blue_Dragon_Film_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Blue_Dragon_Film_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Blue_Dragon_Film_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="South Korea", film_language="Korean", force_rescrape=force
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    run_scraper(conn, force=True)
    conn.close()
