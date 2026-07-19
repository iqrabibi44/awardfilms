"""
Italian scraper — David di Donatello, Venice Film Festival
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_david_di_donatello(conn):
    s = WikiScraper("david-di-donatello", "David di Donatello Awards", "Italy", 1956)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/David_di_Donatello_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/David_di_Donatello_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/David_di_Donatello_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/David_di_Donatello_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Italy", film_language="Italian"
        )

def scrape_venice(conn):
    s = WikiScraper("venice-film-festival", "Venice Film Festival", "Italy", 1932)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Golden Lion", "https://en.wikipedia.org/wiki/Golden_Lion", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Venice_Film_Festival_Award_for_Best_Director", "Directing"),
        ("Volpi Cup Best Actor", "https://en.wikipedia.org/wiki/Volpi_Cup_for_Best_Actor", "Acting"),
        ("Volpi Cup Best Actress", "https://en.wikipedia.org/wiki/Volpi_Cup_for_Best_Actress", "Acting"),
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
    scrape_david_di_donatello(conn)
    scrape_venice(conn)
    conn.close()
