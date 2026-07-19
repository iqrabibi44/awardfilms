"""
scrape_filmfare_south_telugu.py
Scrapes all Telugu-wing Filmfare Awards South category pages from Wikipedia.
"""

from common import fetch_wikipedia_html, get_tables, write_csv, write_gaps, page_url, log
from table_parser import parse_award_table

AWARD_SHOW = "Filmfare Awards South"
LANGUAGE = "Telugu"

# (Wikipedia page title, category label, has_role_column)
CATEGORIES = [
    ("Filmfare Award for Best Film – Telugu", "Best Film", False),
    ("Filmfare Award for Best Director – Telugu", "Best Director", False),
    ("Filmfare Award for Best Actor – Telugu", "Best Actor", True),
    ("Filmfare Award for Best Actress – Telugu", "Best Actress", True),
    ("Filmfare Award for Best Supporting Actor – Telugu", "Best Supporting Actor", True),
    ("Filmfare Award for Best Supporting Actress – Telugu", "Best Supporting Actress", True),
    ("Filmfare Award for Best Music Director – Telugu", "Best Music Director", False),
    ("Filmfare Award for Best Lyricist – Telugu", "Best Lyricist", False),
    ("Filmfare Award for Best Male Playback Singer – Telugu", "Best Male Playback Singer", False),
    ("Filmfare Award for Best Female Playback Singer – Telugu", "Best Female Playback Singer", False),
    ("Filmfare Award for Best Comedian – Telugu", "Best Comedian", True),
    ("Filmfare Award for Best Villain – Telugu", "Best Villain", True),
    ("Filmfare Critics Award for Best Film – Telugu", "Critics Best Film", False),
    ("Filmfare Critics Award for Best Actor – Telugu", "Critics Best Actor", True),
    ("Filmfare Critics Award for Best Actress – Telugu", "Critics Best Actress", True),
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
            for item in parse_award_table(table, has_role_column=has_role):
                if not item["year"]:
                    continue
                found_any = True
                rows.append([
                    AWARD_SHOW,
                    item["year"],
                    "",
                    category,
                    item["nominee"],
                    item["film"],
                    item["role"],
                    "Winner" if item["is_winner"] else "Nominee",
                    LANGUAGE,
                    url,
                ])

        if not found_any:
            gaps.append([AWARD_SHOW, "", category, "tables present but no rows parsed - check table format manually"])

        log.info("Category '%s' done. Total rows so far: %d", category, len(rows))

    return rows, gaps


if __name__ == "__main__":
    rows, gaps = scrape()
    write_csv(rows, "output/filmfare_south_telugu.csv")
    write_gaps(gaps, "output/filmfare_south_telugu_gaps.csv")
