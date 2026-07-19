"""
Bangladeshi scraper — Bangladesh National Film Awards, Meril Prothom Alo
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_bangladesh_national(conn):
    s = WikiScraper("bangladesh-national-film-awards", "Bangladesh National Film Awards", "Bangladesh", 1975)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Bangladesh_National_Film_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Bangladesh_National_Film_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Bangladesh_National_Film_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Bangladesh_National_Film_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Bangladesh", film_language="Bengali"
        )

def scrape_meril_prothom_alo(conn):
    s = WikiScraper("meril-prothom-alo-awards", "Meril Prothom Alo Awards", "Bangladesh", 1997)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Meril-Prothom_Alo_Award_for_Best_Film", "Film"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Meril-Prothom_Alo_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Meril-Prothom_Alo_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Bangladesh", film_language="Bengali"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_bangladesh_national(conn)
    scrape_meril_prothom_alo(conn)
    conn.close()
