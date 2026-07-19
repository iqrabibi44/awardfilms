"""
German scraper — German Film Awards, Berlinale
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_german_film_awards(conn):
    s = WikiScraper("german-film-awards", "German Film Awards", "Germany", 1951)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Feature Film", "https://en.wikipedia.org/wiki/German_Film_Award_for_Best_Feature_Film", "Film"),
        ("Best Direction", "https://en.wikipedia.org/wiki/German_Film_Award_for_Best_Direction", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/German_Film_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/German_Film_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Germany", film_language="German"
        )

def scrape_berlinale(conn):
    s = WikiScraper("berlinale", "Berlin International Film Festival", "Germany", 1951)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Golden Bear", "https://en.wikipedia.org/wiki/Golden_Bear", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Silver_Bear_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Silver_Bear_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Silver_Bear_for_Best_Actress", "Acting"),
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
    scrape_german_film_awards(conn)
    scrape_berlinale(conn)
    conn.close()
