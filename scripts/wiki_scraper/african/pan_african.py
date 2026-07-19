"""
Pan-African scraper — FESPACO, Carthage, El Gouna
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_fespaco(conn):
    s = WikiScraper("fespaco", "FESPACO", "Burkina Faso", 1969, frequency="biennial")
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("General", "https://en.wikipedia.org/wiki/FESPACO", "Film"),
        ("Étalon de Yennenga", "https://en.wikipedia.org/wiki/Etalon_de_Yennenga", "Film"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept
        )

def scrape_carthage(conn):
    s = WikiScraper("carthage-film-festival", "Carthage Film Festival", "Tunisia", 1966, frequency="biennial")
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("General", "https://en.wikipedia.org/wiki/Carthage_Film_Festival", "Film"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept
        )

def scrape_el_gouna(conn):
    s = WikiScraper("el-gouna-film-festival", "El Gouna Film Festival", "Egypt", 2017)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("General", "https://en.wikipedia.org/wiki/El_Gouna_Film_Festival", "Film"),
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
    scrape_fespaco(conn)
    scrape_carthage(conn)
    scrape_el_gouna(conn)
    conn.close()
