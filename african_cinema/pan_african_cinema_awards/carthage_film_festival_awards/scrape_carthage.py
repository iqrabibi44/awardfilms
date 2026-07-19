import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
import random

TOR_SOCKS_PORT = 9050
HEADERS = {
    "User-Agent": "PanAfricanCinemaScraper/2.0 (educational data science project; contact: student_scraper@example.com)"
}

# Tanit d'Or page + Carthage main page
CARTHAGE_URLS = [
    "https://en.wikipedia.org/wiki/Carthage_Film_Festival",
    "https://en.wikipedia.org/wiki/Tanit_d%27or",
    "https://en.wikipedia.org/wiki/Carthage_Film_Festival_Award_for_Best_Director",
    "https://en.wikipedia.org/wiki/Carthage_Film_Festival_Award_for_Best_Actor",
    "https://en.wikipedia.org/wiki/Carthage_Film_Festival_Award_for_Best_Actress",
    "https://en.wikipedia.org/wiki/Carthage_Film_Festival_Award_for_Best_Short_Film",
    "https://en.wikipedia.org/wiki/Carthage_Film_Festival_Award_for_Best_Documentary",
]

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\[[^\]]+\]', '', str(text))
    text = text.replace('†', '').replace('*', '').replace('‡', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_proxies(thread_id=0):
    return {
        "http": f"socks5h://user_{thread_id}:pass_{thread_id}@127.0.0.1:{TOR_SOCKS_PORT}",
        "https": f"socks5h://user_{thread_id}:pass_{thread_id}@127.0.0.1:{TOR_SOCKS_PORT}",
    }

def fetch_page(url, proxies, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, proxies=proxies, timeout=45)
            if resp.status_code == 200:
                return resp.text
        except Exception as e:
            if attempt == retries - 1:
                print(f"    Failed: {url}: {e}")
            time.sleep(random.uniform(1.0, 3.0))
    return None

def parse_edition_from_cell(cell_text):
    """Extract year from edition string like '1st', '4-11December 1966' etc."""
    year_m = re.search(r'\b(19|20)\d{2}\b', cell_text)
    return int(year_m.group()) if year_m else None

def split_multiple_winners(text):
    """Split a cell containing multiple winners like 'Film A by Dir A\nFilm B by Dir B'."""
    text = clean_text(text)
    if not text or text.lower() in ("not awarded", "n/a", "-"):
        return []
    # Split on line breaks or capital letter after period
    parts = re.split(r'\n|(?<=[.!?])\s+(?=[A-Z])', text)
    results = []
    for part in parts:
        part = part.strip()
        if part and len(part) > 2 and part.lower() not in ("not awarded", "n/a", "-"):
            results.append(part)
    return results if results else [text]

def parse_film_director_country(text):
    """Parse 'Film Title by Director (Country)' or 'Film Title\nDirector\nCountry'."""
    text = clean_text(text)
    film = ""
    director = ""
    country = ""

    # Try 'by' pattern
    by_m = re.split(r'\s+by\s+', text, maxsplit=1, flags=re.IGNORECASE)
    if len(by_m) == 2:
        film = clean_text(by_m[0])
        rest = clean_text(by_m[1])
        country_m = re.search(r'\(([^)]+)\)\s*$', rest)
        if country_m:
            country = clean_text(country_m.group(1))
            director = clean_text(re.sub(r'\s*\([^)]+\)\s*$', '', rest))
        else:
            director = rest
    else:
        film = text

    return film, director, country

def parse_carthage_main_table(table, source_url):
    """
    Parse the main Carthage editions table with columns:
    Edition | Dates | Tanit d'or | Tanit d'argent | Tanit de bronze
    """
    records = []
    rows = table.find_all("tr")
    headers = []

    for row in rows:
        cells = row.find_all(["th", "td"])
        if not cells:
            continue

        # Header row
        if all(c.name == "th" for c in cells):
            headers = [clean_text(c.get_text()) for c in cells]
            continue

        cell_texts = [clean_text(c.get_text()) for c in cells]
        if len(cell_texts) < 2:
            continue

        # Get year from Edition or Dates column
        year = None
        if headers:
            for i, h in enumerate(headers):
                if "edition" in h.lower() or "date" in h.lower() or "year" in h.lower():
                    if i < len(cell_texts):
                        year = parse_edition_from_cell(cell_texts[i])
                        if year:
                            break

        if not year:
            # Try first two cells
            for ct in cell_texts[:2]:
                year = parse_edition_from_cell(ct)
                if year:
                    break

        if not year:
            continue

        ceremony_name = f"Carthage Film Festival {year}"

        # Map award columns to categories
        award_cols = {}
        if headers:
            for i, h in enumerate(headers):
                h_low = h.lower()
                if "tanit d'or" in h_low or "tanit d'or" in h_low or "gold" in h_low:
                    award_cols["Tanit d'Or (Golden Tanit)"] = i
                elif "tanit d'argent" in h_low or "silver" in h_low or "argent" in h_low:
                    award_cols["Tanit d'Argent (Silver Tanit)"] = i
                elif "tanit de bronze" in h_low or "bronze" in h_low:
                    award_cols["Tanit de Bronze (Bronze Tanit)"] = i

        if not award_cols:
            # Default fallback: columns 2,3,4 are Tanit d'Or, Argent, Bronze
            categories = ["Tanit d'Or (Golden Tanit)", "Tanit d'Argent (Silver Tanit)", "Tanit de Bronze (Bronze Tanit)"]
            for i, cat in enumerate(categories):
                if i + 2 < len(cell_texts):
                    award_cols[cat] = i + 2

        for category, col_idx in award_cols.items():
            if col_idx >= len(cell_texts):
                continue
            cell_val = cell_texts[col_idx]
            if not cell_val or cell_val.lower() in ("not awarded", "n/a", "-", ""):
                continue

            # Each cell may have multiple winners separated by newlines
            winners = split_multiple_winners(cell_val)
            is_winner = "Or" in category or "Gold" in category

            for winner_text in winners:
                film, director, country = parse_film_director_country(winner_text)
                if film:
                    records.append({
                        "year": year,
                        "ceremony": ceremony_name,
                        "category": category,
                        "nominee": director,
                        "film": film,
                        "country": country,
                        "winner": 1 if is_winner else 0,
                        "source_url": source_url
                    })

    return records

def parse_category_table(table, source_url, default_category="Award"):
    """
    Parse individual category pages like Tanit d'Or page.
    Columns: Year | Film | Director/Filmmaker | Country | Result
    """
    records = []
    rows = table.find_all("tr")
    headers = []
    current_year = None

    for row in rows:
        cells = row.find_all(["th", "td"])
        if not cells:
            continue

        if all(c.name == "th" for c in cells):
            headers = [clean_text(c.get_text()) for c in cells]
            continue

        cell_texts = [clean_text(c.get_text()) for c in cells]
        if not any(cell_texts):
            continue

        is_winner = any(c.find(["b", "strong"]) for c in cells)

        # Map columns
        film = ""
        director = ""
        country = ""
        year = None

        if headers:
            col_map = {h.lower(): (v, i) for i, (h, v) in enumerate(zip(headers, cell_texts))}
            # Year
            for yk in ["year", "edition", "date"]:
                if yk in col_map:
                    yr_m = re.search(r'\b(19|20)\d{2}\b', col_map[yk][0])
                    if yr_m:
                        year = int(yr_m.group())
                    break
            # Film
            for fk in ["film", "title", "movie"]:
                if fk in col_map:
                    film = col_map[fk][0]
                    break
            # Director
            for dk in ["director", "filmmaker", "director/filmmaker", "person"]:
                if dk in col_map:
                    director = col_map[dk][0]
                    break
            # Country
            for ck in ["country", "nationality", "nation"]:
                if ck in col_map:
                    country = col_map[ck][0]
                    break
            # Result
            for rk in ["result", "award", "status"]:
                if rk in col_map:
                    res = col_map[rk][0].lower()
                    if res in ("won", "winner", "awarded"):
                        is_winner = True
                    break
        
        # Fallback: detect year in first cell
        if not year and cell_texts:
            yr_m = re.search(r'\b(19|20)\d{2}\b', cell_texts[0])
            if yr_m:
                year = int(yr_m.group())
                current_year = year
            elif current_year:
                year = current_year

        if not year:
            continue

        current_year = year

        if not film and len(cell_texts) >= 2:
            film = cell_texts[1] if len(cell_texts) > 1 else cell_texts[0]
        if not director and len(cell_texts) >= 3:
            director = cell_texts[2]
        if not country and len(cell_texts) >= 4:
            country = cell_texts[3]

        if not film:
            continue

        ceremony_name = f"Carthage Film Festival {year}"
        records.append({
            "year": year,
            "ceremony": ceremony_name,
            "category": default_category,
            "nominee": director,
            "film": film,
            "country": country,
            "winner": 1 if is_winner else 0,
            "source_url": source_url
        })

    return records

def parse_page(html, source_url):
    soup = BeautifulSoup(html, "lxml")
    records = []

    tables = soup.find_all("table", class_=re.compile("wikitable"))
    for table in tables:
        prev_h = table.find_previous(["h2", "h3", "h4"])
        category = clean_text(prev_h.get_text()) if prev_h else "Award"

        # Check if this is the main editions table (has Tanit columns)
        first_row = table.find("tr")
        if first_row:
            header_text = clean_text(first_row.get_text()).lower()
            if "tanit" in header_text or "edition" in header_text:
                records.extend(parse_carthage_main_table(table, source_url))
                continue

        # Individual category table
        exclude = {"contents", "references", "external links", "see also"}
        if category.lower() in exclude:
            category = "Award"
        records.extend(parse_category_table(table, source_url, default_category=category))

    # Also parse lists under headings
    headings = soup.find_all(["h2", "h3", "h4"])
    for heading in headings:
        category = clean_text(heading.get_text())
        exclude = {"contents", "references", "external links", "see also", "history", "program and awards", "editions"}
        if category.lower() in exclude or len(category) > 100:
            continue

        year_in_heading = None
        yr_m = re.search(r'\b(19|20)\d{2}\b', category)
        if yr_m:
            year_in_heading = int(yr_m.group())

        start_elem = heading
        if heading.parent and heading.parent.name == "div" and any(
            cls.startswith("mw-heading") for cls in heading.parent.get("class", [])
        ):
            start_elem = heading.parent

        sibling = start_elem.next_sibling
        while sibling:
            sname = getattr(sibling, 'name', None)
            if not sname:
                sibling = sibling.next_sibling
                continue
            if sname in ("h2", "h3", "h4"):
                break
            if sname == "div" and any(cls.startswith("mw-heading") for cls in sibling.get("class", [])):
                break

            if sname == "ul":
                for li in sibling.find_all("li"):
                    li_text = clean_text(li.get_text())
                    if not li_text or len(li_text) < 3:
                        continue
                    is_winner = bool(li.find(["b", "strong"]))
                    yr_m2 = re.search(r'\b(19|20)\d{2}\b', li_text)
                    year = int(yr_m2.group()) if yr_m2 else year_in_heading
                    if not year:
                        continue
                    film, director, country = parse_film_director_country(li_text)
                    if film:
                        records.append({
                            "year": year,
                            "ceremony": f"Carthage Film Festival {year}",
                            "category": category,
                            "nominee": director,
                            "film": film,
                            "country": country,
                            "winner": 1 if is_winner else 0,
                            "source_url": source_url
                        })
            sibling = sibling.next_sibling

    return records

def main():
    print("[*] Starting Carthage Film Festival scraping run...")
    proxies = get_proxies(0)

    try:
        ip = requests.get("https://icanhazip.com", proxies=proxies, timeout=15).text.strip()
        print(f"[*] Tor IP: {ip}")
    except Exception:
        pass

    all_records = []
    for url in CARTHAGE_URLS:
        print(f"[*] Fetching: {url}")
        html = fetch_page(url, proxies)
        if html:
            recs = parse_page(html, url)
            print(f"    Parsed {len(recs)} records.")
            all_records.extend(recs)
        else:
            print(f"    Not available.")
        time.sleep(random.uniform(0.5, 1.5))

    df = pd.DataFrame(all_records)
    if not df.empty:
        df = df.drop_duplicates(subset=["year", "category", "nominee", "film"])
        df = df.sort_values(by=["year", "category", "winner", "nominee"], ascending=[True, True, False, True])

        import csv
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(output_dir, "carthage_awards.csv")
        df.to_csv(output_path, index=False, quoting=csv.QUOTE_MINIMAL)
        print(f"\n[+] Carthage data saved: {output_path}")
        print(f"    Total unique records: {len(df)}")
        print(f"    Years: {sorted(df['year'].unique())}")
        print(f"\n    By category:")
        print(df.groupby("category")["film"].count().to_string())
    else:
        print("[-] No records scraped.")

if __name__ == "__main__":
    main()
