"""
French scraper — César Awards, Cannes
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_cesar(conn):
    s = WikiScraper("cesar-awards", "César Awards", "France", 1976)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/C%C3%A9sar_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/C%C3%A9sar_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/C%C3%A9sar_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/C%C3%A9sar_Award_for_Best_Actress", "Acting"),
        ("Best Supporting Actor", "https://en.wikipedia.org/wiki/C%C3%A9sar_Award_for_Best_Supporting_Actor", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/C%C3%A9sar_Award_for_Best_Supporting_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="France", film_language="French"
        )

def scrape_cannes(conn):
    s = WikiScraper("cannes", "Cannes Film Festival", "France", 1946)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Palme d'Or", "https://en.wikipedia.org/wiki/Palme_d%27Or", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Cannes_Film_Festival_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Cannes_Film_Festival_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Cannes_Film_Festival_Award_for_Best_Actress", "Acting"),
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
    scrape_cesar(conn)
    scrape_cannes(conn)
    conn.close()
