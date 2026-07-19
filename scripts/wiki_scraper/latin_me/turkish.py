"""
Turkish scraper — Antalya Golden Orange Film Awards
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_antalya(conn):
    s = WikiScraper("antalya-golden-orange", "Antalya Golden Orange Film Awards", "Turkey", 1963)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("General", "https://en.wikipedia.org/wiki/Antalya_Golden_Orange_Film_Festival", "Film"),
        ("Best Film", "https://en.wikipedia.org/wiki/Golden_Orange_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Golden_Orange_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Golden_Orange_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Golden_Orange_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Turkey", film_language="Turkish"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_antalya(conn)
    conn.close()
