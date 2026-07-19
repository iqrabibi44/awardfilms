"""
Spanish scraper — Goya Awards
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_goya(conn):
    s = WikiScraper("goya-awards", "Goya Awards", "Spain", 1987)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Goya_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Goya_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Goya_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Goya_Award_for_Best_Actress", "Acting"),
        ("Best Supporting Actor", "https://en.wikipedia.org/wiki/Goya_Award_for_Best_Supporting_Actor", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/Goya_Award_for_Best_Supporting_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Spain", film_language="Spanish"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_goya(conn)
    conn.close()
