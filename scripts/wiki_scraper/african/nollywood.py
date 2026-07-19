"""
Nollywood scraper — AMAA, AMVCA, Best of Nollywood
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_amaa(conn):
    s = WikiScraper("amaa", "African Movie Academy Awards", "Nigeria", 2005)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/African_Movie_Academy_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/African_Movie_Academy_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/African_Movie_Academy_Award_for_Best_Actor_in_a_Leading_Role", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/African_Movie_Academy_Award_for_Best_Actress_in_a_Leading_Role", "Acting"),
        ("Best Supporting Actor", "https://en.wikipedia.org/wiki/African_Movie_Academy_Award_for_Best_Supporting_Actor", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/African_Movie_Academy_Award_for_Best_Supporting_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Nigeria"
        )

def scrape_amvca(conn):
    s = WikiScraper("amvca", "Africa Magic Viewers Choice Awards", "Nigeria", 2013)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Movie", "https://en.wikipedia.org/wiki/Africa_Magic_Viewers%27_Choice_Award_for_Best_Movie", "Film"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Africa_Magic_Viewers%27_Choice_Award_for_Best_Actor_in_a_Movie", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Africa_Magic_Viewers%27_Choice_Award_for_Best_Actress_in_a_Movie", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Nigeria"
        )

def scrape_best_of_nollywood(conn):
    s = WikiScraper("best-of-nollywood-awards", "Best of Nollywood Awards", "Nigeria", 2006)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("General", "https://en.wikipedia.org/wiki/Best_of_Nollywood_Awards", "Film"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Nigeria"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_amaa(conn)
    scrape_amvca(conn)
    scrape_best_of_nollywood(conn)
    conn.close()
