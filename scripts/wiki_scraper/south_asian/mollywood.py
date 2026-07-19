"""
Mollywood scraper — Kerala State, Asianet, SIIMA Malayalam
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_kerala_state(conn):
    s = WikiScraper("kerala-state-film-awards", "Kerala State Film Awards", "India", 1969)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Kerala_State_Film_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Kerala_State_Film_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Kerala_State_Film_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Kerala_State_Film_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Malayalam"
        )

def scrape_asianet(conn):
    s = WikiScraper("asianet-film-awards", "Asianet Film Awards", "India", 2009)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Asianet_Film_Awards_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Asianet_Film_Awards_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Asianet_Film_Awards_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Asianet_Film_Awards_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Malayalam"
        )

def scrape_siima_malayalam(conn):
    s = WikiScraper("siima-awards-malayalam", "SIIMA Awards Malayalam", "India", 2012)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/SIIMA_Award_for_Best_Film_Malayalam", "Film"),
        ("Best Actor", "https://en.wikipedia.org/wiki/SIIMA_Award_for_Best_Actor_Malayalam", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/SIIMA_Award_for_Best_Actress_Malayalam", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Malayalam"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_kerala_state(conn)
    scrape_asianet(conn)
    scrape_siima_malayalam(conn)
    conn.close()
