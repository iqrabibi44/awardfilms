"""
Japanese scraper — Japan Academy, Kinema Junpo, Mainichi
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_japan_academy(conn):
    s = WikiScraper("japan-academy-film-prize", "Japan Academy Film Prize", "Japan", 1978)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Outstanding Film", "https://en.wikipedia.org/wiki/Japan_Academy_Film_Prize_for_Outstanding_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Japan_Academy_Film_Prize_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Japan_Academy_Film_Prize_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Japan_Academy_Film_Prize_for_Best_Actress", "Acting"),
        ("Best Supporting Actor", "https://en.wikipedia.org/wiki/Japan_Academy_Film_Prize_for_Best_Supporting_Actor", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/Japan_Academy_Film_Prize_for_Best_Supporting_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Japan", film_language="Japanese"
        )

def scrape_kinema_junpo(conn):
    s = WikiScraper("kinema-junpo-awards", "Kinema Junpo Awards", "Japan", 1924)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Kinema_Junpo_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Kinema_Junpo_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Kinema_Junpo_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Kinema_Junpo_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Japan", film_language="Japanese"
        )

def scrape_mainichi(conn):
    s = WikiScraper("mainichi-film-awards", "Mainichi Film Awards", "Japan", 1947)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Mainichi_Film_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Mainichi_Film_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Mainichi_Film_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Mainichi_Film_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Japan", film_language="Japanese"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_japan_academy(conn)
    scrape_kinema_junpo(conn)
    scrape_mainichi(conn)
    conn.close()
