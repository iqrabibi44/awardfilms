"""
Sandalwood scraper — Karnataka State, SIIMA Kannada
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_karnataka_state(conn):
    s = WikiScraper("karnataka-state-film-awards", "Karnataka State Film Awards", "India", 1967)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Karnataka_State_Film_Award_for_Best_Film", "Film"),
        ("Best Direction", "https://en.wikipedia.org/wiki/Karnataka_State_Film_Award_for_Best_Direction", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Karnataka_State_Film_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Karnataka_State_Film_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Kannada"
        )

def scrape_siima_kannada(conn):
    s = WikiScraper("siima-awards-kannada", "SIIMA Awards Kannada", "India", 2012)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/SIIMA_Award_for_Best_Film_Kannada", "Film"),
        ("Best Actor", "https://en.wikipedia.org/wiki/SIIMA_Award_for_Best_Actor_Kannada", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/SIIMA_Award_for_Best_Actress_Kannada", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Kannada"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_karnataka_state(conn)
    scrape_siima_kannada(conn)
    conn.close()
