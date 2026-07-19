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

ZIFF_URLS = [
    "https://en.wikipedia.org/wiki/Zanzibar_International_Film_Festival",
    "https://en.wikipedia.org/wiki/Golden_Dhow",
    "https://en.wikipedia.org/wiki/Zanzibar_International_Film_Festival_Award_for_Best_Documentary",
    "https://en.wikipedia.org/wiki/Zanzibar_International_Film_Festival_Award_for_Best_Short_Film",
    "https://en.wikipedia.org/wiki/Zanzibar_International_Film_Festival_Award_for_Best_Actor",
    "https://en.wikipedia.org/wiki/Zanzibar_International_Film_Festival_Award_for_Best_Actress",
    "https://en.wikipedia.org/wiki/Zanzibar_International_Film_Festival_Award_for_Best_Director",
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

def parse_table(table, source_url, default_category="Award"):
    records = []
    rows = table.find_all("tr")
    headers = []
    current_year = None

    for row in rows:
        cells = row.find_all(["th", "td"])
        if not cells:
            continue

        if all(c.name == "th" for c in cells):
            if len(cells) == 1:
                cat = clean_text(cells[0].get_text())
                if cat and cat.lower() not in ("year", "film", "director", "country", "result"):
                    default_category = cat
            else:
                headers = [clean_text(c.get_text()) for c in cells]
            continue

        cell_texts = [clean_text(c.get_text()) for c in cells]
        if not any(cell_texts):
            continue

        is_winner = any(c.find(["b", "strong"]) for c in cells)

        film = ""
        director = ""
        country = ""
        year = None

        if headers:
            col_map = {}
            for h, v in zip(headers, cell_texts):
                col_map[h.lower()] = v

            for yk in ["year", "edition"]:
                if yk in col_map:
                    yr_m = re.search(r'\b(19|20)\d{2}\b', col_map[yk])
                    if yr_m:
                        year = int(yr_m.group())
                    break

            for fk in ["film", "title", "movie"]:
                if fk in col_map:
                    film = col_map[fk]
                    break

            for dk in ["director", "filmmaker", "director(s)", "director/filmmaker"]:
                if dk in col_map:
                    director = col_map[dk]
                    break

            for ck in ["country", "country of origin", "nation"]:
                if ck in col_map:
                    country = col_map[ck]
                    break

            for rk in ["result", "award", "status"]:
                if rk in col_map:
                    res = col_map[rk].lower()
                    if res in ("won", "winner", "awarded"):
                        is_winner = True
                    break

        # Fallback: use cell positions
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
            film = cell_texts[1]
        if not director and len(cell_texts) >= 3:
            director = cell_texts[2]
        if not country and len(cell_texts) >= 4:
            country = cell_texts[3]

        if not film:
            continue

        ceremony_name = f"ZIFF {year}"
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

    # All wikitables
    tables = soup.find_all("table", class_=re.compile("wikitable"))
    for table in tables:
        prev_h = table.find_previous(["h2", "h3", "h4"])
        category = clean_text(prev_h.get_text()) if prev_h else "Award"
        exclude = {"contents", "references", "external links", "see also", "history"}
        if category.lower() in exclude:
            category = "Award"
        records.extend(parse_table(table, source_url, default_category=category))

    # Lists under headings
    headings = soup.find_all(["h2", "h3", "h4"])
    for heading in headings:
        category = clean_text(heading.get_text())
        exclude = {"contents", "references", "external links", "see also", "history", "awards"}
        if category.lower() in exclude or len(category) > 100:
            continue

        yr_m = re.search(r'\b(19|20)\d{2}\b', category)
        year_in_heading = int(yr_m.group()) if yr_m else None

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

                    # Try 'Film by Director (Country)'
                    by_m = re.split(r'\s+by\s+', li_text, maxsplit=1, flags=re.IGNORECASE)
                    if len(by_m) == 2:
                        film = clean_text(by_m[0])
                        rest = clean_text(by_m[1])
                        country_m = re.search(r'\(([^)]+)\)\s*$', rest)
                        country = clean_text(country_m.group(1)) if country_m else ""
                        director = clean_text(re.sub(r'\s*\([^)]+\)\s*$', '', rest))
                    else:
                        parts = [p.strip() for p in li_text.split(',')]
                        film = parts[0]
                        director = parts[1] if len(parts) > 1 else ""
                        country = ""

                    if film:
                        records.append({
                            "year": year,
                            "ceremony": f"ZIFF {year}",
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
    print("[*] Starting Zanzibar IFF scraping run...")
    proxies = get_proxies(0)

    try:
        ip = requests.get("https://icanhazip.com", proxies=proxies, timeout=15).text.strip()
        print(f"[*] Tor IP: {ip}")
    except Exception:
        pass

    all_records = []
    for url in ZIFF_URLS:
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
        output_path = os.path.join(output_dir, "zanzibar_iff_awards.csv")
        df.to_csv(output_path, index=False, quoting=csv.QUOTE_MINIMAL)
        print(f"\n[+] ZIFF data saved: {output_path}")
        print(f"    Total unique records: {len(df)}")
        print(f"    Years: {sorted(df['year'].unique())}")
        print(f"\n    By category:")
        print(df.groupby("category")["film"].count().to_string())
    else:
        print("[-] No records scraped.")

if __name__ == "__main__":
    main()
