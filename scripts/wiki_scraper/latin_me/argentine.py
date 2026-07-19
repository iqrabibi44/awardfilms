"""
Argentine scraper — Cóndor de Plata
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_condor(conn):
    s = WikiScraper("condor-de-plata", "Cóndor de Plata Awards", "Argentina", 1943)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/C%C3%B3ndor_de_Plata_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/C%C3%B3ndor_de_Plata_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/C%C3%B3ndor_de_Plata_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/C%C3%B3ndor_de_Plata_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Argentina", film_language="Spanish"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_condor(conn)
    conn.close()
