"""
scrape_vijay_awards.py
Scrapes Vijay Awards (Tamil) categories from Wikipedia.
"""

from common import fetch_wikipedia_html, get_tables, write_csv, write_gaps, page_url, log
from table_parser import parse_award_table

AWARD_SHOW = "Vijay Awards"
LANGUAGE = "Tamil"

CATEGORIES = [
    ("Vijay Award for Best Film", "Best Film", False),
    ("Vijay Award for Best Director", "Best Director", False),
    ("Vijay Award for Best Actor", "Best Actor", True),
    ("Vijay Award for Best Actress", "Best Actress", True),
    ("Vijay Award for Best Supporting Actor", "Best Supporting Actor", True),
    ("Vijay Award for Best Supporting Actress", "Best Supporting Actress", True),
    ("Vijay Award for Best Music Director", "Best Music Director", False),
    ("Vijay Award for Best Lyricist", "Best Lyricist", False),
    ("Vijay Award for Best Male Playback Singer", "Best Male Playback Singer", False),
    ("Vijay Award for Best Female Playback Singer", "Best Female Playback Singer", False),
    ("Vijay Award for Best Comedian", "Best Comedian", True),
    ("Vijay Award for Best Villain", "Best Villain", True),
    ("Vijay Award for Best Debut Director", "Best Debut Director", False),
    ("Vijay Award for Best Debut Actor", "Best Debut Actor", True),
    ("Vijay Award for Best Debut Actress", "Best Debut Actress", True),
    ("Vijay Award for Favourite Hero", "Favourite Hero", True),
    ("Vijay Award for Favourite Heroine", "Favourite Heroine", True),
    ("Vijay Award for Best Cinematographer", "Best Cinematographer", False),
    ("Vijay Award for Best Editor", "Best Editor", False),
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
            gaps.append([AWARD_SHOW, "", category, "tables present but no rows parsed - check table format manually"])

        log.info("Category '%s' done. Total rows so far: %d", category, len(rows))

    return rows, gaps


if __name__ == "__main__":
    rows, gaps = scrape()
    write_csv(rows, "output/vijay_awards.csv")
    write_gaps(gaps, "output/vijay_awards_gaps.csv")
