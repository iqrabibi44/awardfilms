"""
scrape_santosham.py
Scrapes Santosham Film Awards from Wikipedia subpages.
"""
import re
from bs4 import BeautifulSoup
from common import fetch_wikipedia_html, page_url, write_csv, write_gaps, log, clean_text

AWARD_SHOW = "Santosham Film Awards"
LANGUAGE = "Telugu"
MAIN_PAGE = "Santosham Film Awards"

# Map for fallback if Date infobox fails
EDITION_YEAR_MAP = {
    "22nd Santosham Film Awards": 2023,
    "21st Santosham Film Awards": 2022,
    "20th Santosham Film Awards": 2021,
    "17th Santosham Film Awards": 2019,
    "16th Santosham Film Awards": 2018,
    "15th Santosham Film Awards": 2017,
    "14th Santosham Film Awards": 2016,
}

def parse_santosham_table(table, year, edition_name, url):
    rows = table.find_all("tr")
    grid = {}
    max_r = 0
    max_c = 0
    
    for r_idx, tr in enumerate(rows):
        c_idx = 0
        cells = tr.find_all(["td", "th"])
        for cell in cells:
            while (r_idx, c_idx) in grid:
                c_idx += 1
            
            rowspan = int(cell.get("rowspan", 1))
            colspan = int(cell.get("colspan", 1))
            
            for dr in range(rowspan):
                for dc in range(colspan):
                    grid[(r_idx + dr, c_idx + dc)] = cell
                    max_r = max(max_r, r_idx + dr)
                    max_c = max(max_c, c_idx + dc)
            c_idx += colspan

    if max_r == 0 or max_c == 0:
        return []

    # Map headers to column roles
    header_row = 0
    header_cols = []
    for c in range(max_c + 1):
        cell = grid.get((header_row, c))
        header_cols.append(clean_text(cell.get_text()) if cell else "")
    
    cat_col = -1
    nominee_col = -1
    work_col = -1
    
    for c_idx, h in enumerate(header_cols):
        h_lower = h.lower()
        if "category" in h_lower:
            cat_col = c_idx
        elif any(k in h_lower for k in ("recipient", "winner", "name", "actor", "actress", "music director")):
            nominee_col = c_idx
        elif any(k in h_lower for k in ("work", "film", "single", "album")):
            work_col = c_idx

    # If header parsing fails, or if columns are not found, skip table
    if cat_col == -1 or nominee_col == -1:
        return []

    parsed_rows = []
    for r in range(1, max_r + 1):
        cat_cell = grid.get((r, cat_col))
        nominee_cell = grid.get((r, nominee_col))
        work_cell = grid.get((r, work_col)) if work_col != -1 else None
        
        if not cat_cell or not nominee_cell:
            continue
            
        category = clean_text(cat_cell.get_text())
        nominee = clean_text(nominee_cell.get_text())
        work = clean_text(work_cell.get_text()) if work_cell else ""
        
        # Skip header rows repeated inside the table
        if category.lower() == "category" or nominee.lower() in ("recipient", "winner", "name"):
            continue
            
        if not category or not nominee:
            continue
            
        parsed_rows.append([
            AWARD_SHOW, year, edition_name, category,
            nominee, work, "", "Winner",
            LANGUAGE, url
        ])
        
    return parsed_rows

def scrape():
    rows = []
    gaps = []
    
    try:
        log.info("Fetching main Santosham page: %s", MAIN_PAGE)
        main_html = fetch_wikipedia_html(MAIN_PAGE)
    except Exception as e:
        log.error("Could not fetch main Santosham page: %s", e)
        gaps.append([AWARD_SHOW, "", "ALL", f"main page fetch failed: {e}"])
        return rows, gaps

    soup = BeautifulSoup(main_html, "lxml")
    
    # Locate Ceremonies header and extract links
    parent_header = soup.find(id="Ceremonies")
    if not parent_header:
        # Try to find header containing "Ceremonies" text
        for h in soup.find_all(["h2", "h3"]):
            if "ceremonies" in h.text.lower():
                parent_header = h
                break

    if not parent_header:
        log.error("Could not find Ceremonies section on main page.")
        gaps.append([AWARD_SHOW, "", "ALL", "Ceremonies section not found on main page"])
        return rows, gaps

    ul = parent_header.find_next("ul")
    if not ul:
        log.error("Could not find list of ceremonies.")
        gaps.append([AWARD_SHOW, "", "ALL", "No ceremony list found under Ceremonies header"])
        return rows, gaps

    subpages = []
    for a in ul.find_all("a"):
        title = a.get("title")
        if title and ("redlink=1" not in a.get("href", "")):
            subpages.append(title)

    log.info("Found %d Santosham ceremony subpages to scrape.", len(subpages))

    for page in subpages:
        log.info("Scraping subpage: %s", page)
        try:
            html = fetch_wikipedia_html(page)
        except Exception as e:
            log.error("Could not fetch subpage %s: %s", page, e)
            gaps.append([AWARD_SHOW, "", page, f"subpage fetch failed: {e}"])
            continue

        sub_soup = BeautifulSoup(html, "lxml")
        url = page_url(page)
        
        # 1. Determine year from infobox
        year = None
        infobox = sub_soup.find("table", class_="infobox")
        if infobox:
            for tr in infobox.find_all("tr"):
                cells = [c.get_text().strip() for c in tr.find_all(["th", "td"])]
                if len(cells) == 2:
                    label, val = cells
                    if any(k in label.lower() for k in ("date", "year", "held", "films honored")):
                        year_match = re.search(r"\d{4}", val)
                        if year_match:
                            year = int(year_match.group(0))
                            break

        if not year:
            # Fall back to page name mapping
            year = EDITION_YEAR_MAP.get(page)

        if not year:
            # Fall back to regex on page name
            year_match = re.search(r"\d{4}", page)
            if year_match:
                year = int(year_match.group(0))
            else:
                log.warning("Could not determine year for page %s, skipping.", page)
                gaps.append([AWARD_SHOW, "", page, "Could not determine year"])
                continue

        # 2. Extract wikitables
        tables = sub_soup.find_all("table", class_="wikitable")
        log.info("Found %d wikitables on page %s (Year: %d)", len(tables), page, year)
        
        page_rows = 0
        for i, table in enumerate(tables):
            table_rows = parse_santosham_table(table, year, page, url)
            if table_rows:
                rows.extend(table_rows)
                page_rows += len(table_rows)
            else:
                gaps.append([AWARD_SHOW, year, f"{page} - Table {i}", "Table could not be parsed or did not contain awards"])

        log.info("Extracted %d rows from %s", page_rows, page)

    return rows, gaps

if __name__ == "__main__":
    rows, gaps = scrape()
    write_csv(rows, "output/santosham_awards.csv")
    write_gaps(gaps, "output/santosham_awards_gaps.csv")
