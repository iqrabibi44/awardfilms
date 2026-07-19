"""
Lollywood scraper — Lux Style, ARY, Hum, Nigar, Tarang Housefull
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_lux_style(conn):
    s = WikiScraper("lux-style-awards", "Lux Style Awards", "Pakistan", 2002)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Lux_Style_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Lux_Style_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Lux_Style_Award_for_Best_Actor_Film", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Lux_Style_Award_for_Best_Actress_Film", "Acting"),
        ("Best Supporting Actor", "https://en.wikipedia.org/wiki/Lux_Style_Award_for_Best_Supporting_Actor", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/Lux_Style_Award_for_Best_Supporting_Actress", "Acting"),
        ("Best Villain", "https://en.wikipedia.org/wiki/Lux_Style_Award_for_Best_Villain", "Acting"),
        ("Best Playback Singer Male", "https://en.wikipedia.org/wiki/Lux_Style_Award_for_Best_Playback_Singer_Male", "Music"),
        ("Best Playback Singer Female", "https://en.wikipedia.org/wiki/Lux_Style_Award_for_Best_Playback_Singer_Female", "Music"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Pakistan", film_language="Urdu"
        )

def scrape_ary(conn):
    s = WikiScraper("ary-film-awards", "ARY Film Awards", "Pakistan", 2014)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/ARY_Film_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/ARY_Film_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/ARY_Film_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/ARY_Film_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Pakistan", film_language="Urdu"
        )

def scrape_hum(conn):
    s = WikiScraper("hum-awards", "Hum Awards", "Pakistan", 2013)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Hum_Award_for_Best_Film", "Film"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Hum_Award_for_Best_Actor_Film", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Hum_Award_for_Best_Actress_Film", "Acting"),
        ("Best Director", "https://en.wikipedia.org/wiki/Hum_Award_for_Best_Director", "Directing"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Pakistan", film_language="Urdu"
        )

def scrape_nigar(conn):
    s = WikiScraper("nigar-awards", "Nigar Awards", "Pakistan", 1957)
    ceremony_id = s.upsert_ceremony(conn)

    # Nigar Awards are highly variable; these general pages hold all info
    categories = [
        ("General", "https://en.wikipedia.org/wiki/Nigar_Award", "Film"),
        ("Archives", "https://en.wikipedia.org/wiki/Nigar_Awards", "Film"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Pakistan", film_language="Urdu"
        )

def scrape_tarang_housefull(conn):
    s = WikiScraper("tarang-housefull-awards", "Tarang Housefull Awards", "Pakistan", 2013)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("General", "https://en.wikipedia.org/wiki/Tarang_Housefull_Awards", "Film"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="Pakistan", film_language="Urdu"
        )


if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_lux_style(conn)
    scrape_ary(conn)
    scrape_hum(conn)
    scrape_nigar(conn)
    scrape_tarang_housefull(conn)
    conn.close()
