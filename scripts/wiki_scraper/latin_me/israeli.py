"""
Israeli scraper — Ophir Awards
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_ophir(conn):
    s = WikiScraper("ophir-awards", "Israeli Film Academy Awards", "Israel", 1990)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("General", "https://en.wikipedia.org/wiki/Ophir_Award", "Film"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Israel", film_language="Hebrew"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_ophir(conn)
    conn.close()
