"""
scrape_kerala_state_film_awards.py
Scrapes Kerala State Film Awards categories from Wikipedia.
Government-run state award (est. 1969) with decades of history and reasonably
good per-category Wikipedia coverage, but mostly winner-only (no nominees)
for most years - same pattern as Nandi Awards / TN State Film Awards.
"""

from common import fetch_wikipedia_html, get_tables, write_csv, write_gaps, page_url, log
from table_parser import parse_award_table

AWARD_SHOW = "Kerala State Film Awards"
LANGUAGE = "Malayalam"

CATEGORIES = [
    ("Kerala State Film Award for Best Film", "Best Film", False),
    ("Kerala State Film Award for Best Director", "Best Director", False),
    ("Kerala State Film Award for Best Actor", "Best Actor", True),
    ("Kerala State Film Award for Best Actress", "Best Actress", True),
    ("Kerala State Film Award for Best Supporting Actor", "Best Supporting Actor", True),
    ("Kerala State Film Award for Best Supporting Actress", "Best Supporting Actress", True),
    ("Kerala State Film Award for Best Music Director", "Best Music Director", False),
    ("Kerala State Film Award for Best Male Playback Singer", "Best Male Playback Singer", False),
    ("Kerala State Film Award for Best Female Playback Singer", "Best Female Playback Singer", False),
    ("Kerala State Film Award for Best Lyricist", "Best Lyricist", False),
    ("Kerala State Film Award for Best Cinematographer", "Best Cinematographer", False),
    ("Kerala State Film Award for Best Comedian", "Best Comedian", True),
    ("Kerala State Film Award for Best Child Artist", "Best Child Artist", True),
    ("Kerala State Film Award for Best Screenplay Writer", "Best Screenplay Writer", False),
    ("Kerala State Film Award for Best Editor", "Best Editor", False),
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
    write_csv(rows, "output/kerala_state_film_awards.csv")
    write_gaps(gaps, "output/kerala_state_film_awards_gaps.csv")
