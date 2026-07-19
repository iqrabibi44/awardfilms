"""
Bollywood scraper — Filmfare, IIFA, National Film Awards, Screen, Zee Cine
"""
import sys
import os

# Add parent directory to path so we can import base
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_filmfare(conn):
    s = WikiScraper("filmfare-awards", "Filmfare Awards", "India", 1954)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Actress", "Acting"),
        ("Best Supporting Actor", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Supporting_Actor", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Supporting_Actress", "Acting"),
        ("Best Story", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Story", "Writing"),
        ("Best Screenplay", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Screenplay", "Writing"),
        ("Best Music Album", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Music_Album", "Music"),
        ("Best Playback Singer Male", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Playback_Singer_Male", "Music"),
        ("Best Playback Singer Female", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Playback_Singer_Female", "Music"),
        ("Best Debut Male", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Debut_Male", "Acting"),
        ("Best Debut Female", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Debut_Female", "Acting"),
        ("Best Action", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Action", "Technical"),
        ("Best Art Direction", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Art_Direction", "Technical"),
        ("Best Background Score", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Background_Score", "Music"),
        ("Best Choreography", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Choreography", "Technical"),
        ("Best Cinematography", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Cinematography", "Technical"),
        ("Best Costume Design", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Costume_Design", "Technical"),
        ("Best Dialogue", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Dialogue", "Writing"),
        ("Best Editing", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Editing", "Technical"),
        ("Best Lyricist", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Lyricist", "Music"),
        ("Best Sound Design", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Sound_Design", "Technical"),
        ("Best Special Effects", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Special_Effects", "Technical"),
        ("Best Performance in a Negative Role", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Performance_in_a_Negative_Role", "Acting"),
        ("Best Performance in a Comic Role", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Performance_in_a_Comic_Role", "Acting"),
        ("Critics Award for Best Film", "https://en.wikipedia.org/wiki/Filmfare_Critics_Award_for_Best_Film", "Film"),
        ("Critics Award for Best Actor", "https://en.wikipedia.org/wiki/Filmfare_Critics_Award_for_Best_Actor", "Acting"),
        ("Critics Award for Best Actress", "https://en.wikipedia.org/wiki/Filmfare_Critics_Award_for_Best_Actress", "Acting"),
        ("Lifetime Achievement Award", "https://en.wikipedia.org/wiki/Filmfare_Lifetime_Achievement_Award", "Honorary"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Hindi"
        )


def scrape_iifa(conn):
    s = WikiScraper("iifa-awards", "IIFA Awards", "India", 2000)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Actor_in_a_Leading_Role_Male", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Actor_in_a_Leading_Role_Female", "Acting"),
        ("Best Supporting Actor", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Supporting_Actor", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Supporting_Actress", "Acting"),
        ("Best Performance in a Negative Role", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Performance_in_a_Negative_Role", "Acting"),
        ("Best Performance in a Comic Role", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Performance_in_a_Comic_Role", "Acting"),
        ("Best Music Director", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Music_Director", "Music"),
        ("Best Lyricist", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Lyricist", "Music"),
        ("Best Male Playback Singer", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Male_Playback_Singer", "Music"),
        ("Best Female Playback Singer", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Female_Playback_Singer", "Music"),
        ("Best Story", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Story", "Writing"),
        ("Best Screenplay", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Screenplay", "Writing"),
        ("Best Dialogue", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Dialogue", "Writing"),
        ("Best Cinematography", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Cinematography", "Technical"),
        ("Best Choreography", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Choreography", "Technical"),
        ("Best Editing", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Editing", "Technical"),
        ("Best Sound Recording", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Sound_Recording", "Technical"),
        ("Best Sound Re-Recording", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Sound_Re-Recording", "Technical"),
        ("Best Special Effects", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Special_Effects", "Technical"),
        ("Best Art Direction", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Art_Direction", "Technical"),
        ("Best Action", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Action", "Technical"),
        ("Best Makeup", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Makeup", "Technical"),
        ("Best Costume Design", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Costume_Design", "Technical"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Hindi"
        )


def scrape_national(conn):
    s = WikiScraper("national-film-awards-india", "National Film Awards", "India", 1954)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Feature Film", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Feature_Film", "Film"),
        ("Best Direction", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Direction", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Actress", "Acting"),
        ("Best Supporting Actor", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Supporting_Actor", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Supporting_Actress", "Acting"),
        ("Best Popular Film", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Popular_Film", "Film"),
        ("Best Children's Film", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Children%27s_Film", "Film"),
        ("Best Music Direction", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Music_Direction", "Music"),
        ("Best Male Playback Singer", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Male_Playback_Singer", "Music"),
        ("Best Female Playback Singer", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Female_Playback_Singer", "Music"),
        ("Best Cinematography", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Cinematography", "Technical"),
        ("Best Screenplay", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Screenplay", "Writing"),
        ("Best Audiography", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Audiography", "Technical"),
        ("Best Editing", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Editing", "Technical"),
        ("Best Art Direction", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Art_Direction", "Technical"),
        ("Best Costume Design", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Costume_Design", "Technical"),
        ("Best Make-up Artist", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Make-up_Artist", "Technical"),
        ("Best Choreography", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Choreography", "Technical"),
        ("Best Special Effects", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Special_Effects", "Technical"),
        ("Best Lyrics", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Lyrics", "Music"),
        ("Best Child Artist", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Child_Artist", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India" # Language varies widely here
        )

def scrape_screen(conn):
    s = WikiScraper("screen-awards", "Screen Awards", "India", 1994)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Actor", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Actress", "Acting"),
        ("Best Supporting Actor", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Supporting_Actor", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Supporting_Actress", "Acting"),
        ("Best Actor in a Negative Role", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Actor_in_a_Negative_Role", "Acting"),
        ("Best Actor in a Comic Role", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Actor_in_a_Comic_Role", "Acting"),
        ("Best Music Director", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Music_Director", "Music"),
        ("Best Male Playback", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Male_Playback", "Music"),
        ("Best Female Playback", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Female_Playback", "Music"),
        ("Best Lyricist", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Lyricist", "Music"),
        ("Best Story", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Story", "Writing"),
        ("Best Screenplay", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Screenplay", "Writing"),
        ("Best Dialogue", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Dialogue", "Writing"),
        ("Best Editing", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Editing", "Technical"),
        ("Best Cinematography", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Cinematography", "Technical"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Hindi"
        )


def scrape_zee_cine(conn):
    s = WikiScraper("zee-cine-awards", "Zee Cine Awards", "India", 1998)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Actor_Male", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Actor_Female", "Acting"),
        ("Best Actor in a Supporting Role", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Actor_in_a_Supporting_Role_%E2%80%93_Male", "Acting"),
        ("Best Actress in a Supporting Role", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Actor_in_a_Supporting_Role_%E2%80%93_Female", "Acting"),
        ("Best Performance in a Negative Role", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Performance_in_a_Negative_Role", "Acting"),
        ("Best Performance in a Comic Role", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Performance_in_a_Comic_Role", "Acting"),
        ("Best Music Director", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Music_Director", "Music"),
        ("Best Lyricist", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Lyricist", "Music"),
        ("Best Playback Singer Male", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Playback_Singer_%E2%80%93_Male", "Music"),
        ("Best Playback Singer Female", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Playback_Singer_%E2%80%93_Female", "Music"),
        ("Best Story", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Story", "Writing"),
        ("Best Screenplay", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Screenplay", "Writing"),
        ("Best Dialogue", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Dialogue", "Writing"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Hindi"
        )


def scrape_stardust(conn):
    s = WikiScraper("stardust-awards", "Stardust Awards", "India", 1970)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Stardust_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Stardust_Award_for_Best_Director", "Directing"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Stardust_Award_for_Best_Actress", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/Stardust_Award_for_Best_Supporting_Actress", "Acting"),
        ("Best Actor in a Comedy or Romance", "https://en.wikipedia.org/wiki/Stardust_Award_for_Best_Actor_in_a_Comedy_or_Romance", "Acting"),
        ("Best Actor in a Drama", "https://en.wikipedia.org/wiki/Stardust_Award_for_Best_Actor_in_a_Drama", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Hindi"
        )


def scrape_producers_guild(conn):
    s = WikiScraper("producers-guild", "Producers Guild Film Awards", "India", 2004)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/Producers_Guild_Film_Award_for_Best_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/Producers_Guild_Film_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/Producers_Guild_Film_Award_for_Best_Actor_in_a_Leading_Role", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/Producers_Guild_Film_Award_for_Best_Actress_in_a_Leading_Role", "Acting"),
        ("Best Supporting Actor", "https://en.wikipedia.org/wiki/Producers_Guild_Film_Award_for_Best_Actor_in_a_Supporting_Role", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/Producers_Guild_Film_Award_for_Best_Actress_in_a_Supporting_Role", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="India", film_language="Hindi"
        )

if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_filmfare(conn)
    scrape_iifa(conn)
    scrape_national(conn)
    scrape_screen(conn)
    scrape_zee_cine(conn)
    scrape_stardust(conn)
    scrape_producers_guild(conn)
    conn.close()
