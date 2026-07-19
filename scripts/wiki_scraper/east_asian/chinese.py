"""
Chinese scraper — Golden Rooster, Hundred Flowers
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_golden_rooster(conn):
    s = WikiScraper("golden-rooster-awards", "Golden Rooster Awards", "China", 1981)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Picture", "https://en.wikipedia.org/wiki/Golden_Rooster_Award_for_Best_Picture", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Golden_Rooster_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Golden_Rooster_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Golden_Rooster_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="China", film_language="Mandarin"
        )

def scrape_hundred_flowers(conn):
    s = WikiScraper("hundred-flowers-awards", "Hundred Flowers Awards", "China", 1962)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Hundred_Flowers_Award_for_Best_Film", "Film"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Hundred_Flowers_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Hundred_Flowers_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="China", film_language="Mandarin"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_golden_rooster(conn)
    scrape_hundred_flowers(conn)
    conn.close()
