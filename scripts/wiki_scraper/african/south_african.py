"""
South African scraper — SAFTA, Durban IFF
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_safta(conn):
    s = WikiScraper("safta", "South African Film and Television Awards", "South Africa", 2006)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("General", "https://en.wikipedia.org/wiki/South_African_Film_and_Television_Awards", "Film"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="South Africa"
        )

def scrape_durban_iff(conn):
    s = WikiScraper("durban-iff", "Durban International Film Festival", "South Africa", 1978)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("General", "https://en.wikipedia.org/wiki/Durban_International_Film_Festival", "Film"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="South Africa"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_safta(conn)
    scrape_durban_iff(conn)
    conn.close()
