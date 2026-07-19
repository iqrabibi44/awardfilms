"""
scrape_suvarna_film_awards.py
Scrapes Suvarna Film Awards (est. 2007, run by Suvarna TV channel).
Like Asianet/Vanitha in the Mollywood set, this is a TV-channel-run award
with thinner Wikipedia/structured-web coverage than Filmfare/SIIMA/state
awards. Built to fail loudly into gaps_log rather than fabricate data -
expect to need manual sourcing from Suvarna's own site or Kannada
entertainment news archives for gaps.
"""

from common import fetch_wikipedia_html, get_tables, write_csv, write_gaps, page_url, log
from table_parser import parse_award_table

AWARD_SHOW = "Suvarna Film Awards"
LANGUAGE = "Kannada"

MAIN_PAGE = "Suvarna Film Awards"

# Add (page_title, category, has_role_column) tuples here if individual
# category pages are confirmed to exist on Wikipedia.
CATEGORIES = []


def scrape():
    rows = []
    gaps = []

    for page_title, category, has_role in CATEGORIES:
        url = page_url(page_title)
        try:
            html = fetch_wikipedia_html(page_title)
        except Exception as e:  # noqa: BLE001
            gaps.append([AWARD_SHOW, "", category, f"page fetch failed: {e}"])
            continue
        for table in get_tables(html):
            for item in parse_award_table(table, has_role_column=has_role, winners_only=True):
                if not item["year"]:
                    continue
                rows.append([
                    AWARD_SHOW, item["year"], "", category,
                    item["nominee"], item["film"], item["role"],
                    "Winner" if item["is_winner"] else "Nominee",
                    LANGUAGE, url,
                ])

    url = page_url(MAIN_PAGE)
    try:
        html = fetch_wikipedia_html(MAIN_PAGE)
        tables = get_tables(html)
        if not tables:
            gaps.append([AWARD_SHOW, "", "ALL", "main page exists but has no wikitable - data may be prose-only"])
        for table in tables:
            parsed_any = False
            for item in parse_award_table(table, has_role_column=True, winners_only=True):
                if not item["year"]:
                    continue
                parsed_any = True
                rows.append([
                    AWARD_SHOW, item["year"], "", "Unspecified (verify category from source)",
                    item["nominee"], item["film"], item["role"],
                    "Winner" if item["is_winner"] else "Nominee",
                    LANGUAGE, url,
                ])
            if not parsed_any:
                gaps.append([AWARD_SHOW, "", "ALL", "table found but parser could not extract rows - manual review needed"])
    except Exception as e:  # noqa: BLE001
        log.warning("No usable Wikipedia page for Suvarna Film Awards: %s", e)
        gaps.append([AWARD_SHOW, "", "ALL",
                     f"main page fetch failed: {e} -- source manually from Suvarna TV / Kannada news archives"])

    return rows, gaps


if __name__ == "__main__":
    rows, gaps = scrape()
    write_csv(rows, "output/suvarna_film_awards.csv")
    write_gaps(gaps, "output/suvarna_film_awards_gaps.csv")
