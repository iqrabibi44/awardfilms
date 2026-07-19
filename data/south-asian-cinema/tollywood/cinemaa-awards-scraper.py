"""
scrape_cinemaa.py
Scrapes CineMAA Awards categories from Wikipedia. CineMAA's Wikipedia coverage is
sparser than Filmfare/Nandi - many years only exist as a single "list of winners"
article rather than per-category pages. This script tries category pages first,
then falls back to a single list page.
"""

from common import fetch_wikipedia_html, get_tables, write_csv, write_gaps, page_url, log
from table_parser import parse_award_table

AWARD_SHOW = "CineMAA Awards"
LANGUAGE = "Telugu"

CATEGORIES = [
    ("CineMAA Award for Best Film", "Best Film", False),
    ("CineMAA Award for Best Director", "Best Director", False),
    ("CineMAA Award for Best Actor", "Best Actor", True),
    ("CineMAA Award for Best Actress", "Best Actress", True),
    ("CineMAA Award for Best Music Director", "Best Music Director", False),
]

# Fallback single page that historically lists all CineMAA winners by year/category
LIST_FALLBACK_PAGE = "CineMAA Awards"


def scrape():
    rows = []
    gaps = []
    any_category_worked = False

    for page_title, category, has_role in CATEGORIES:
        url = page_url(page_title)
        try:
            html = fetch_wikipedia_html(page_title)
        except Exception as e:  # noqa: BLE001
            log.warning("Category page missing for '%s': %s", category, e)
            gaps.append([AWARD_SHOW, "", category, f"category page fetch failed: {e}"])
            continue

        tables = get_tables(html)
        for table in tables:
            for item in parse_award_table(table, has_role_column=has_role, winners_only=True):
                if not item["year"]:
                    continue
                any_category_worked = True
                rows.append([
                    AWARD_SHOW, item["year"], "", category,
                    item["nominee"], item["film"], item["role"],
                    "Winner" if item["is_winner"] else "Nominee",
                    LANGUAGE, url,
                ])

    if not any_category_worked:
        log.info("No category pages worked, falling back to main list page: %s", LIST_FALLBACK_PAGE)
        url = page_url(LIST_FALLBACK_PAGE)
        try:
            html = fetch_wikipedia_html(LIST_FALLBACK_PAGE)
            tables = get_tables(html)
            for table in tables:
                # Best-effort generic parse; treat first col as category/year, manual review expected
                for tr in table.find_all("tr"):
                    cells = tr.find_all(["td", "th"])
                    texts = [c.get_text(" ", strip=True) for c in cells]
                    if len(texts) >= 3:
                        rows.append([
                            AWARD_SHOW, texts[0], "", "Unspecified (see source)",
                            texts[1], texts[2] if len(texts) > 2 else "",
                            "", "Winner", LANGUAGE, url,
                        ])
        except Exception as e:  # noqa: BLE001
            gaps.append([AWARD_SHOW, "", "ALL", f"fallback list page failed: {e}"])

    return rows, gaps


if __name__ == "__main__":
    rows, gaps = scrape()
    write_csv(rows, "output/cinemaa_awards.csv")
    write_gaps(gaps, "output/cinemaa_awards_gaps.csv")
