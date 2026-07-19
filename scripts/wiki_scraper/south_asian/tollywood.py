"""
Tollywood scraper — Filmfare South, Nandi, SIIMA Telugu
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_filmfare_south(conn):
    s = WikiScraper("filmfare-awards-south", "Filmfare Awards South", "India", 1972)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Filmfare_Award_South_for_Best_Film_Telugu", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Filmfare_Award_South_for_Best_Director_Telugu", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Filmfare_Award_South_for_Best_Actor_Telugu", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Filmfare_Award_South_for_Best_Actress_Telugu", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Telugu"
        )

def scrape_nandi(conn):
    s = WikiScraper("nandi-awards", "Nandi Awards", "India", 1964)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Feature Film", "https://en.wikipedia.org/wiki/Nandi_Award_for_Best_Feature_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Nandi_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Nandi_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Nandi_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Telugu"
        )

def scrape_siima_telugu(conn):
    s = WikiScraper("siima-awards-telugu", "SIIMA Awards Telugu", "India", 2012)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/SIIMA_Award_for_Best_Film_Telugu", "Film"),
        ("Best Actor", "https://en.wikipedia.org/wiki/SIIMA_Award_for_Best_Actor_Telugu", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/SIIMA_Award_for_Best_Actress_Telugu", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Telugu"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_filmfare_south(conn)
    scrape_nandi(conn)
    scrape_siima_telugu(conn)
    conn.close()
