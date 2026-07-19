"""
scrape_sun_kudumbam.py
Scrapes Sun Kudumbam Viridhugal (Sun TV's Tamil film/TV awards).
NOTE: Sun Kudumbam Viridhugal has very thin Wikipedia/structured-web coverage
compared to Vijay Awards or SIIMA. Expect this scraper to produce mostly gaps
on the first run - it's built to fail loudly into gaps_log rather than silently,
so you can see exactly what needs manual sourcing (likely Sun TV's own site,
or Tamil entertainment news archives like Dinamalar/Dinakaran/Behindwoods).
"""

from common import fetch_wikipedia_html, get_tables, write_csv, write_gaps, page_url, log
from table_parser import parse_award_table

AWARD_SHOW = "Sun Kudumbam Viridhugal"
LANGUAGE = "Tamil"

MAIN_PAGE = "Sun Kudumbam Viruthugal"

# If individual category pages turn out to exist on Wikipedia, add them here
# in the same (page_title, category, has_role_column) format used by other scrapers.
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

    # Fallback: try the single main Wikipedia article (if it exists at all)
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
        log.warning("No usable Wikipedia page for Sun Kudumbam Viridhugal: %s", e)
        gaps.append([AWARD_SHOW, "", "ALL",
                     f"main page fetch failed: {e} -- source manually from Sun TV / Behindwoods / Dinamalar archives"])

    return rows, gaps


if __name__ == "__main__":
    rows, gaps = scrape()
    write_csv(rows, "output/sun_kudumbam_viridhugal.csv")
    write_gaps(gaps, "output/sun_kudumbam_viridhugal_gaps.csv")
