"""
Brazilian scraper — Grande Otelo, Gramado
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_grande_otelo(conn):
    s = WikiScraper("grande-otelo-awards", "Grande Otelo Awards", "Brazil", 2001)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Grande_Otelo_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Grande_Otelo_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Grande_Otelo_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Grande_Otelo_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Brazil", film_language="Portuguese"
        )

def scrape_gramado(conn):
    s = WikiScraper("gramado-film-festival", "Gramado Film Festival", "Brazil", 1973)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("General", "https://en.wikipedia.org/wiki/Gramado_Film_Festival", "Film"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Brazil", film_language="Portuguese"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_grande_otelo(conn)
    scrape_gramado(conn)
    conn.close()
