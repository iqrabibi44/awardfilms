import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from base import WikiScraper

def run_scraper(conn, force=False):
    s = WikiScraper("baeksang-arts-awards", "Baeksang Arts Awards", "South Korea", 1965)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Baeksang_Arts_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Baeksang_Arts_Award_for_Best_Director_–_Film", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Baeksang_Arts_Award_for_Best_Actor_–_Film", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Baeksang_Arts_Award_for_Best_Actress_–_Film", "Acting"),
        ("Best Supporting Actor", "https://en.wikipedia.org/wiki/Baeksang_Arts_Award_for_Best_Supporting_Actor_–_Film", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/Baeksang_Arts_Award_for_Best_Supporting_Actress_–_Film", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="South Korea", film_language="Korean", force_rescrape=force
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    run_scraper(conn, force=True)
    conn.close()
