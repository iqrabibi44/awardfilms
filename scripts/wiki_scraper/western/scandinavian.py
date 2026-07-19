"""
Scandinavian scraper — Guldbagge Awards
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_guldbagge(conn):
    s = WikiScraper("guldbagge-awards", "Guldbagge Awards", "Sweden", 1964)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Guldbagge_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Guldbagge_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Guldbagge_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Guldbagge_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Sweden", film_language="Swedish"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_guldbagge(conn)
    conn.close()
