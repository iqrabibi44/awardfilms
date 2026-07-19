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

EL_GOUNA_MAIN = "https://en.wikipedia.org/wiki/El_Gouna_Film_Festival"
EL_GOUNA_CATEGORY_PAGES = [
    ("https://en.wikipedia.org/wiki/El_Gouna_Film_Festival_Award_for_Best_Feature_Narrative", "Best Feature Narrative Film"),
    ("https://en.wikipedia.org/wiki/El_Gouna_Film_Festival_Award_for_Best_Feature_Documentary", "Best Feature Documentary"),
    ("https://en.wikipedia.org/wiki/El_Gouna_Film_Festival_Award_for_Best_Short_Film", "Best Short Film"),
    ("https://en.wikipedia.org/wiki/El_Gouna_Film_Festival_Award_for_Best_Arab_Short_Film", "Best Arab Short Film"),
    ("https://en.wikipedia.org/wiki/El_Gouna_Film_Festival_Award_for_Best_Arab_Film", "Best Arab Film"),
    ("https://en.wikipedia.org/wiki/El_Gouna_Film_Festival_Award_for_Best_Director", "Best Director"),
    ("https://en.wikipedia.org/wiki/El_Gouna_Film_Festival_Award_for_Best_Actor", "Best Actor"),
    ("https://en.wikipedia.org/wiki/El_Gouna_Film_Festival_Award_for_Best_Actress", "Best Actress"),
    ("https://en.wikipedia.org/wiki/CineGouna_Platform", "CineGouna Platform"),
    ("https://en.wikipedia.org/wiki/El_Gouna_Star", "El Gouna Star"),
]

WINNER_AWARDS = {"golden star", "first prize", "gold", "winner", "awarded", "el gouna star for best"}

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\[[^\]]+\]', '', str(text))
    text = text.replace('†', '').replace('*', '').replace('‡', '').replace('[edit]', '')
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
    current_category = default_category

    for row in rows:
        cells = row.find_all(["th", "td"])
        if not cells:
            continue

        if all(c.name == "th" for c in cells):
            if len(cells) == 1:
                cat = clean_text(cells[0].get_text())
                if cat and cat.lower() not in ("year", "film", "director", "result", "award"):
                    current_category = cat
            else:
                headers = [clean_text(c.get_text()) for c in cells]
            continue

        cell_texts = [clean_text(c.get_text()) for c in cells]
        if not any(cell_texts):
            continue

        is_winner = any(c.find(["b", "strong"]) for c in cells)
        film, director, country, year, award_name = "", "", "", None, ""

        if headers:
            col_map = {h.lower(): v for h, v in zip(headers, cell_texts)}
            for yk in ["year", "edition"]:
                if yk in col_map:
                    yr_m = re.search(r'\b(20\d{2})\b', col_map[yk])
                    if yr_m:
                        year = int(yr_m.group())
                    break
            film = col_map.get("film", col_map.get("title", col_map.get("movie", "")))
            director = col_map.get("director", col_map.get("filmmaker", ""))
            country = col_map.get("country", "")
            award_name = col_map.get("award", col_map.get("prize", ""))
            result = col_map.get("result", col_map.get("status", ""))
            if result.lower() in ("won", "winner", "awarded"):
                is_winner = True

        if not year and cell_texts:
            yr_m = re.search(r'\b(20\d{2})\b', cell_texts[0])
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

        ceremony_name = f"El Gouna Film Festival {year}"
        records.append({
            "year": year,
            "ceremony": ceremony_name,
            "category": current_category,
            "award": award_name,
            "nominee": director,
            "film": film,
            "country": country,
            "winner": 1 if is_winner else 0,
            "source_url": source_url
        })

    return records

def parse_section_winners(section_text, year, ceremony_name, competition_category, source_url):
    """Parse section text: Award: Film, Director"""
    records = []
    section_text = re.sub(r'\[edit\]', '', section_text)

    award_pattern = re.compile(
        r'(Golden Star|Silver Star|Bronze Star|El Gouna Star[^:\n]{0,50}|'
        r'Best[^:\n]{0,50}|Special[^:\n]{0,40}|Jury[^:\n]{0,40}|'
        r'First Prize|Second Prize|Third Prize|Honorable Mention[^:\n]{0,20}|'
        r'FIPRESCI[^:\n]{0,20}|Netpac[^:\n]{0,20}|Award[^:\n]{0,20})\s*:',
        re.IGNORECASE
    )

    parts = award_pattern.split(section_text)
    i = 1
    while i < len(parts) - 1:
        award_name = clean_text(parts[i])
        rest = clean_text(parts[i + 1])

        if not award_name or not rest:
            i += 2
            continue

        rest_clean = rest.split('\n')[0].strip()
        comma_parts = [p.strip() for p in rest_clean.split(',')]
        if len(comma_parts) >= 2:
            director = comma_parts[-1]
            film = ', '.join(comma_parts[:-1])
        else:
            film = rest_clean
            director = ""

        film = clean_text(film)
        director = clean_text(director)

        if not film or len(film) < 2:
            i += 2
            continue

        is_winner = any(w in award_name.lower() for w in WINNER_AWARDS)
        records.append({
            "year": year,
            "ceremony": ceremony_name,
            "category": competition_category,
            "award": award_name,
            "nominee": director,
            "film": film,
            "country": "",
            "winner": 1 if is_winner else 0,
            "source_url": source_url
        })
        i += 2

    return records

def parse_main_page(html, source_url):
    soup = BeautifulSoup(html, "lxml")
    records = []

    headings = soup.find_all(["h2", "h3"])
    for heading in headings:
        heading_text = clean_text(heading.get_text())
        year_match = re.search(r'\b(20\d{2})\b', heading_text)
        if not year_match or "winner" not in heading_text.lower():
            continue

        year = int(year_match.group())
        ceremony_name = f"El Gouna Film Festival {year}"
        current_competition = "Award"

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
            if sname == "h2":
                break
            if sname == "div" and any(cls.startswith("mw-heading") for cls in sibling.get("class", [])):
                inner = sibling.find("h2")
                if inner:
                    break

            if sname == "h3":
                current_competition = clean_text(sibling.get_text())
                sibling = sibling.next_sibling
                continue

            if sname == "section":
                sec_h = sibling.find(["h3", "h2"])
                if sec_h:
                    current_competition = clean_text(sec_h.get_text())
                section_text = sibling.get_text(separator="\n")
                recs = parse_section_winners(section_text, year, ceremony_name, current_competition, source_url)
                records.extend(recs)

            if sname == "ul":
                for li in sibling.find_all("li"):
                    li_text = clean_text(li.get_text())
                    colon_idx = li_text.find(':')
                    if colon_idx > 0:
                        award_name = li_text[:colon_idx].strip()
                        rest = li_text[colon_idx+1:].strip()
                        comma_parts = [p.strip() for p in rest.split(',')]
                        film = ', '.join(comma_parts[:-1]) if len(comma_parts) >= 2 else rest
                        director = comma_parts[-1] if len(comma_parts) >= 2 else ""
                        is_winner = any(w in award_name.lower() for w in WINNER_AWARDS)
                        if film:
                            records.append({
                                "year": year,
                                "ceremony": ceremony_name,
                                "category": current_competition,
                                "award": award_name,
                                "nominee": director,
                                "film": film,
                                "country": "",
                                "winner": 1 if is_winner else 0,
                                "source_url": source_url
                            })

            # Wikitables
            if sname == "table" and "wikitable" in " ".join(sibling.get("class", [])):
                records.extend(parse_table(sibling, source_url, default_category=current_competition))

            sibling = sibling.next_sibling

    # Also parse ALL wikitables on page
    for table in soup.find_all("table", class_=re.compile("wikitable")):
        prev_h = table.find_previous(["h2", "h3", "h4"])
        category = clean_text(prev_h.get_text()) if prev_h else "Award"
        yr_m = re.search(r'\b(20\d{2})\b', category)
        year = int(yr_m.group()) if yr_m else None
        if not year:
            continue
        records.extend(parse_table(table, source_url, default_category=category))

    return records

def parse_category_page(html, source_url, category_name):
    soup = BeautifulSoup(html, "lxml")
    records = []
    for table in soup.find_all("table", class_=re.compile("wikitable")):
        records.extend(parse_table(table, source_url, default_category=category_name))
    return records

def main():
    print("[*] Starting El Gouna Film Festival scraping run...")
    proxies = get_proxies(0)

    try:
        ip = requests.get("https://icanhazip.com", proxies=proxies, timeout=15).text.strip()
        print(f"[*] Tor IP: {ip}")
    except Exception:
        pass

    all_records = []

    # Main page (2017-2021 section-based winners)
    print(f"[*] Fetching main page: {EL_GOUNA_MAIN}")
    html = fetch_page(EL_GOUNA_MAIN, proxies)
    if html:
        recs = parse_main_page(html, EL_GOUNA_MAIN)
        print(f"    Parsed {len(recs)} records from main page.")
        all_records.extend(recs)

    # Category-specific pages
    for url, cat_name in EL_GOUNA_CATEGORY_PAGES:
        print(f"[*] Fetching: {url}")
        html = fetch_page(url, proxies)
        if html:
            recs = parse_category_page(html, url, cat_name)
            print(f"    Parsed {len(recs)} records.")
            all_records.extend(recs)
        else:
            print(f"    Not available.")
        time.sleep(random.uniform(0.5, 1.5))

    df = pd.DataFrame(all_records)
    if not df.empty:
        df = df[df["film"].str.len() > 2]
        df = df.drop_duplicates(subset=["year", "category", "nominee", "film"])
        df = df.sort_values(by=["year", "category", "winner", "nominee"], ascending=[True, True, False, True])

        import csv
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(output_dir, "el_gouna_awards.csv")
        df.to_csv(output_path, index=False, quoting=csv.QUOTE_MINIMAL)
        print(f"\n[+] El Gouna data saved: {output_path}")
        print(f"    Total unique records: {len(df)}")
        print(f"    Years: {sorted(df['year'].unique())}")
        print(f"\n    By year:")
        print(df.groupby("year")["film"].count().to_string())
    else:
        print("[-] No records.")

if __name__ == "__main__":
    main()
