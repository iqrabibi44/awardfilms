import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

TOR_SOCKS_PORT = 9050
HEADERS = {
    "User-Agent": "BritishCinemaScraper/1.0 (educational data science project; contact: student_scraper@example.com)"
}

BAFTA_URLS = {
    "Best Film": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Film",
    "Best British Film": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_British_Film",
    "Best Direction": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Direction",
    "Best Actor in a Leading Role": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Actor_in_a_Leading_Role",
    "Best Actress in a Leading Role": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Actress_in_a_Leading_Role",
    "Best Actor in a Supporting Role": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Actor_in_a_Supporting_Role",
    "Best Actress in a Supporting Role": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Actress_in_a_Supporting_Role",
    "Best Original Screenplay": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Original_Screenplay",
    "Best Adapted Screenplay": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Adapted_Screenplay"
}

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

def parse_bafta_table(table, category, source_url):
    records = []
    rows = table.find_all("tr")
    headers = []
    current_year = None

    for row in rows:
        cells = row.find_all(["th", "td"])
        if not cells:
            continue

        if all(c.name == "th" for c in cells):
            if len(cells) > 1:
                headers = [clean_text(c.get_text()) for c in cells]
            continue

        cell_texts = [clean_text(c.get_text()) for c in cells]
        if not any(cell_texts):
            continue

        is_winner = False
        row_style = row.get("style", "")
        if "background:#FAEB86" in row_style or "background:#B0C4DE" in row_style:
            is_winner = True
        elif any(c.find(["b", "strong"]) for c in cells):
            is_winner = True
        elif any("background" in c.get("style", "").lower() for c in cells if c.get("style")):
            is_winner = True

        film = ""
        nominee = ""
        country = ""
        year = None

        if headers:
            col_map = {h.lower(): v for h, v in zip(headers, cell_texts)}
            # Find year
            for yk in ["year", "ceremony"]:
                if yk in col_map:
                    yr_m = re.search(r'\b(19|20)\d{2}\b', col_map[yk])
                    if yr_m:
                        year = int(yr_m.group())
                    break
            
            # Find film
            for fk in ["film", "title", "motion picture"]:
                if fk in col_map:
                    film = col_map[fk]
                    break
            
            # Find nominee
            for nk in ["director", "actor", "actress", "screenwriter", "nominee", "recipient"]:
                if nk in col_map:
                    nominee = col_map[nk]
                    break
                    
            # Find country
            for ck in ["country", "nation"]:
                if ck in col_map:
                    country = col_map[ck]
                    break

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

        # Fallbacks for columns
        if not film:
            if "actor" in category.lower() or "actress" in category.lower():
                if len(cell_texts) >= 3:
                    nominee = cell_texts[1] if not nominee else nominee
                    film = cell_texts[2]
            else:
                if len(cell_texts) >= 2:
                    film = cell_texts[1]
                if len(cell_texts) >= 3:
                    nominee = cell_texts[2] if not nominee else nominee

        if film or nominee:
            if not film: film = nominee
            ceremony_name = f"BAFTA {year}"
            records.append({
                "year": year,
                "ceremony": ceremony_name,
                "category": category,
                "nominee": nominee,
                "film": film,
                "country": country,
                "winner": 1 if is_winner else 0,
                "source_url": source_url
            })

    return records

def parse_page(url, category, thread_id):
    proxies = get_proxies(thread_id)
    html = fetch_page(url, proxies)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    records = []
    
    # Process only wikitables that look like award tables
    tables = soup.find_all("table", class_=re.compile("wikitable"))
    for table in tables:
        # Check if table headers look like award headers
        first_row = table.find("tr")
        if first_row:
            headers = [clean_text(th.get_text()).lower() for th in first_row.find_all("th")]
            if any(h in ["film", "actor", "actress", "director", "recipient", "nominee", "year"] for h in headers):
                records.extend(parse_bafta_table(table, category, url))

    return records

def main():
    print("[*] Starting BAFTA Film Awards scraping...")
    
    all_records = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_cat = {
            executor.submit(parse_page, url, cat, i % 5): cat
            for i, (cat, url) in enumerate(BAFTA_URLS.items())
        }
        for future in as_completed(future_to_cat):
            cat = future_to_cat[future]
            try:
                recs = future.result()
                print(f"[+] {cat}: parsed {len(recs)} records.")
                all_records.extend(recs)
            except Exception as e:
                print(f"[-] {cat} failed: {e}")

    df = pd.DataFrame(all_records)
    if not df.empty:
        df = df.drop_duplicates(subset=["year", "category", "nominee", "film"])
        df = df.sort_values(by=["year", "category", "winner", "nominee"], ascending=[True, True, False, True])

        import csv
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(output_dir, "bafta_awards.csv")
        df.to_csv(output_path, index=False, quoting=csv.QUOTE_MINIMAL)
        print(f"\n[+] BAFTA data saved: {output_path}")
        print(f"    Total unique records: {len(df)}")
        print(f"    Years: {sorted(df['year'].unique())[:5]}...{sorted(df['year'].unique())[-5:]}")
    else:
        print("[-] No records scraped.")

if __name__ == "__main__":
    main()
