"""
Kollywood scraper — Vijay Awards, Tamil Nadu State, SIIMA Tamil
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_vijay(conn):
    s = WikiScraper("vijay-awards", "Vijay Awards", "India", 2006)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Vijay_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Vijay_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Vijay_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Vijay_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Tamil"
        )

def scrape_tamil_nadu(conn):
    s = WikiScraper("tamil-nadu-state-film-awards", "Tamil Nadu State Film Awards", "India", 1967)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Tamil_Nadu_State_Film_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Tamil_Nadu_State_Film_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Tamil_Nadu_State_Film_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Tamil_Nadu_State_Film_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Tamil"
        )

def scrape_siima_tamil(conn):
    s = WikiScraper("siima-awards-tamil", "SIIMA Awards Tamil", "India", 2012)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/SIIMA_Award_for_Best_Film_Tamil", "Film"),
        ("Best Actor", "https://en.wikipedia.org/wiki/SIIMA_Award_for_Best_Actor_Tamil", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/SIIMA_Award_for_Best_Actress_Tamil", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Tamil"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_vijay(conn)
    scrape_tamil_nadu(conn)
    scrape_siima_tamil(conn)
    conn.close()
