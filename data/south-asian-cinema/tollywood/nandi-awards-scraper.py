"""
scrape_nandi.py
Scrapes Nandi Awards (Andhra Pradesh state film awards) categories from Wikipedia.
Nandi Awards date back to the 1960s and are organized as per-category pages,
e.g. "Nandi Award for Best Feature Film", "Nandi Award for Best Actor".
"""

from common import fetch_wikipedia_html, get_tables, write_csv, write_gaps, page_url, log
from table_parser import parse_award_table

AWARD_SHOW = "Nandi Awards"
LANGUAGE = "Telugu"

CATEGORIES = [
    ("Nandi Award for Best Feature Film", "Best Feature Film", False),
    ("Nandi Award for Best Director", "Best Director", False),
    ("Nandi Award for Best Actor", "Best Actor", True),
    ("Nandi Award for Best Actress", "Best Actress", True),
    ("Nandi Award for Best Male Comedian", "Best Male Comedian", True),
    ("Nandi Award for Best Female Comedian", "Best Female Comedian", True),
    ("Nandi Award for Best Villain", "Best Villain", True),
    ("Nandi Award for Best Music Director", "Best Music Director", False),
    ("Nandi Award for Best Male Playback Singer", "Best Male Playback Singer", False),
    ("Nandi Award for Best Female Playback Singer", "Best Female Playback Singer", False),
    ("Nandi Award for Best Lyricist", "Best Lyricist", False),
    ("Nandi Award for Best Cinematographer", "Best Cinematographer", False),
    ("Nandi Award for Best Child Actor", "Best Child Actor", True),
    ("Nandi Award for Best Story Writer", "Best Story Writer", False),
]


def scrape():
    rows = []
    gaps = []
    for page_title, category, has_role in CATEGORIES:
        url = page_url(page_title)
        try:
            html = fetch_wikipedia_html(page_title)
        except Exception as e:  # noqa: BLE001
            log.error("Skipping category '%s': %s", category, e)
            gaps.append([AWARD_SHOW, "", category, f"page fetch failed: {e}"])
            continue

        tables = get_tables(html)
        if not tables:
            gaps.append([AWARD_SHOW, "", category, "no wikitable found on page"])
            continue

        found_any = False
        for table in tables:
            for item in parse_award_table(table, has_role_column=has_role, winners_only=True):
                if not item["year"]:
                    continue
                found_any = True
                rows.append([
                    AWARD_SHOW, item["year"], "", category,
                    item["nominee"], item["film"], item["role"],
                    "Winner" if item["is_winner"] else "Nominee",
                    LANGUAGE, url,
                ])
        if not found_any:
            gaps.append([AWARD_SHOW, "", category, "tables present but no rows parsed - check manually"])

        log.info("Category '%s' done. Total rows so far: %d", category, len(rows))

    return rows, gaps


if __name__ == "__main__":
    rows, gaps = scrape()
    write_csv(rows, "output/nandi_awards.csv")
    write_gaps(gaps, "output/nandi_awards_gaps.csv")
