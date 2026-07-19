"""
Arabic scraper — Cairo IFF, DIFF, Marrakech IFF
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_cairo(conn):
    s = WikiScraper("cairo-iff", "Cairo International Film Festival", "Egypt", 1976)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("General", "https://en.wikipedia.org/wiki/Cairo_International_Film_Festival", "Film"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept
        )

def scrape_diff(conn):
    s = WikiScraper("diff", "Dubai International Film Festival", "UAE", 2004)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("General", "https://en.wikipedia.org/wiki/Dubai_International_Film_Festival", "Film"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept
        )

def scrape_marrakech(conn):
    s = WikiScraper("marrakech-iff", "Marrakech International Film Festival", "Morocco", 2001)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("General", "https://en.wikipedia.org/wiki/Marrakech_International_Film_Festival", "Film"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_cairo(conn)
    scrape_diff(conn)
    scrape_marrakech(conn)
    conn.close()
