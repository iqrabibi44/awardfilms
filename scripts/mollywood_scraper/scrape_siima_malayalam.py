"""
scrape_siima_malayalam.py
Scrapes SIIMA (South Indian International Movie Awards) Malayalam-wing categories.
Mirrors scrape_siima.py (Telugu) / scrape_siima_tamil.py (Tamil) - same
category-pages-first, edition-pages-fallback pattern.
"""

from common import fetch_wikipedia_html, get_tables, write_csv, write_gaps, page_url, log, clean_text
from table_parser import parse_award_table

AWARD_SHOW = "SIIMA Awards"
LANGUAGE = "Malayalam"

CATEGORIES = [
    ("SIIMA Award for Best Film – Malayalam", "Best Film", False),
    ("SIIMA Award for Best Actor – Malayalam", "Best Actor", True),
    ("SIIMA Award for Best Actress – Malayalam", "Best Actress", True),
    ("SIIMA Award for Best Director – Malayalam", "Best Director", False),
    ("SIIMA Award for Best Supporting Actor – Malayalam", "Best Supporting Actor", True),
    ("SIIMA Award for Best Supporting Actress – Malayalam", "Best Supporting Actress", True),
    ("SIIMA Award for Best Music Director – Malayalam", "Best Music Director", False),
]

EDITION_PAGES = {
    "12th South Indian International Movie Awards": "2023",
    "11th South Indian International Movie Awards": "2022",
    "10th South Indian International Movie Awards": "2021",
    "9th South Indian International Movie Awards": "2020",
    "8th South Indian International Movie Awards": "2018",
    "7th South Indian International Movie Awards": "2017",
    "6th South Indian International Movie Awards": "2016",
    "5th South Indian International Movie Awards": "2015",
    "4th South Indian International Movie Awards": "2014",
    "3rd South Indian International Movie Awards": "2013",
    "2nd South Indian International Movie Awards": "2012",
}


def scrape_categories():
    rows = []
    gaps = []
    for page_title, category, has_role in CATEGORIES:
        url = page_url(page_title)
        try:
            html = fetch_wikipedia_html(page_title)
        except Exception as e:  # noqa: BLE001
            log.warning("Category page missing for '%s': %s -- will rely on edition pages", category, e)
            gaps.append([AWARD_SHOW, "", category, f"category page fetch failed: {e}"])
            continue

        tables = get_tables(html)
        for table in tables:
            for item in parse_award_table(table, has_role_column=has_role):
                if not item["year"]:
                    continue
                rows.append([
                    AWARD_SHOW, item["year"], "", category,
                    item["nominee"], item["film"], item["role"],
                    "Winner" if item["is_winner"] else "Nominee",
                    LANGUAGE, url,
                ])
    return rows, gaps


def scrape_editions():
    """
    Fallback: parse per-year SIIMA edition pages. These usually mix all four languages
    (Telugu/Tamil/Kannada/Malayalam) in one table. We tag rows and verify.
    """
    rows = []
    gaps = []
    for page_title, year in EDITION_PAGES.items():
        url = page_url(page_title)
        try:
            html = fetch_wikipedia_html(page_title)
        except Exception as e:  # noqa: BLE001
            gaps.append([AWARD_SHOW, page_title, "ALL", f"edition page fetch failed: {e}"])
            continue

        tables = get_tables(html)
        if not tables:
            gaps.append([AWARD_SHOW, year, "ALL", "no wikitable on edition page"])
            continue

        for table in tables:
            for tr in table.find_all("tr"):
                cells = tr.find_all(["td", "th"])
                if len(cells) < 2:
                    continue
                category = clean_text(cells[0].get_text(" ", strip=True))
                winner_cell = clean_text(cells[1].get_text(" ", strip=True))
                if not category or not winner_cell or "category" in category.lower():
                    continue
                
                # Filter out language selector tables, infobox metadata, or hosts/sponsors lists
                category_clean = category.strip(" :-\u2013")
                winner_clean = winner_cell.strip(" :-\u2013")
                
                invalid_terms = {"telugu", "tamil", "kannada", "malayalam", "language", "host", "hosts", "venue", "date", "sponsor", "sponsors", "broadcaster", "broadcasters", "presenter", "presenters", "ceremony"}
                if (category_clean.lower() in invalid_terms or 
                    winner_clean.lower() in invalid_terms or 
                    any(t in category_clean.lower() for t in ("venue", "date", "host", "sponsor"))):
                    continue

                nominee, film = winner_cell, ""
                for sep in [" – ", " - ", " (", "("]:
                    if sep in winner_cell:
                        parts = winner_cell.split(sep, 1)
                        nominee = parts[0].strip()
                        film = parts[1].replace(")", "").strip()
                        break
                rows.append([
                    AWARD_SHOW, year, page_title,
                    category + " [VERIFY: Malayalam-only - edition pages mix languages]",
                    nominee, film, "", "Winner", LANGUAGE, url,
                ])
    return rows, gaps


if __name__ == "__main__":
    cat_rows, cat_gaps = scrape_categories()
    ed_rows, ed_gaps = scrape_editions()

    all_rows = cat_rows + ed_rows
    all_gaps = cat_gaps + ed_gaps

    write_csv(all_rows, "output/siima_malayalam.csv")
    write_gaps(all_gaps, "output/siima_malayalam_gaps.csv")
