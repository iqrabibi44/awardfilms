"""
Hollywood scraper — Golden Globes, SAG Awards, Critics Choice, Independent Spirit
(Note: Oscars are handled via Kaggle CSV pipeline in root scripts folder)
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper


def scrape_sag_awards(conn):
    s = WikiScraper("sag-awards", "Screen Actors Guild Awards", "United States", 1995)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Outstanding Cast", "https://en.wikipedia.org/wiki/Screen_Actors_Guild_Award_for_Outstanding_Cast_in_a_Motion_Picture", "Film"),
        ("Outstanding Male Actor", "https://en.wikipedia.org/wiki/Screen_Actors_Guild_Award_for_Outstanding_Performance_by_a_Male_Actor_in_a_Leading_Role", "Acting"),
        ("Outstanding Female Actor", "https://en.wikipedia.org/wiki/Screen_Actors_Guild_Award_for_Outstanding_Performance_by_a_Female_Actor_in_a_Leading_Role", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="United States", film_language="English"
        )

def scrape_critics_choice(conn):
    s = WikiScraper("critics-choice-awards", "Critics Choice Awards", "United States", 1995)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Picture", "https://en.wikipedia.org/wiki/Critics%27_Choice_Movie_Award_for_Best_Picture", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Critics%27_Choice_Movie_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Critics%27_Choice_Movie_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Critics%27_Choice_Movie_Award_for_Best_Actress", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="United States", film_language="English"
        )

def scrape_independent_spirit(conn):
    s = WikiScraper("independent-spirit-awards", "Independent Spirit Awards", "United States", 1986)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Feature", "https://en.wikipedia.org/wiki/Independent_Spirit_Award_for_Best_Feature", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Independent_Spirit_Award_for_Best_Director", "Directing"),
        ("Best Male Lead", "https://en.wikipedia.org/wiki/Independent_Spirit_Award_for_Best_Male_Lead", "Acting"),
        ("Best Female Lead", "https://en.wikipedia.org/wiki/Independent_Spirit_Award_for_Best_Female_Lead", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="United States", film_language="English"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()

    scrape_sag_awards(conn)
    scrape_critics_choice(conn)
    scrape_independent_spirit(conn)
    conn.close()
