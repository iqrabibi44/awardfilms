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
    "User-Agent": "GermanCinemaScraper/1.0 (educational data science project; contact: student_scraper@example.com)"
}

BAVARIAN_URLS = {
    "Best Producing": "https://en.wikipedia.org/wiki/Bavarian_Film_Awards_(Best_Producing)",
    "Best Directing": "https://en.wikipedia.org/wiki/Bavarian_Film_Awards_(Best_Directing)",
    "Best Acting": "https://en.wikipedia.org/wiki/Bavarian_Film_Awards_(Best_Acting)",
    "Best Screenplay": "https://en.wikipedia.org/wiki/Bavarian_Film_Awards_(Best_Screenplay)",
    "Best Cinematography": "https://en.wikipedia.org/wiki/Bavarian_Film_Awards_(Best_Cinematography)",
    "Best Editing": "https://en.wikipedia.org/wiki/Bavarian_Film_Awards_(Best_Editing)",
    "Best Film Score": "https://en.wikipedia.org/wiki/Bavarian_Film_Awards_(Best_Film_Score)"
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

def parse_bavarian_table(table, category, source_url):
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
            for fk in ["film", "title", "english title", "original title"]:
                if fk in col_map:
                    film = col_map[fk]
                    break
            
            # Find nominee
            for nk in ["director", "actor", "actress", "winner", "winner(s)"]:
                if nk in col_map:
                    nominee = col_map[nk]
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
            if "actor" in category.lower() or "actress" in category.lower() or "director" in category.lower():
                if len(cell_texts) >= 3:
                    nominee = cell_texts[1] if not nominee else nominee
                    film = cell_texts[2]
                elif len(cell_texts) == 2:
                    nominee = cell_texts[1] if not nominee else nominee
            else:
                if len(cell_texts) >= 3:
                    film = cell_texts[1]
                    nominee = cell_texts[2] if not nominee else nominee
                elif len(cell_texts) == 2:
                    nominee = cell_texts[1] if not nominee else nominee

        if film or nominee:
            if not film: film = nominee
            ceremony_name = f"Bavarian Film Awards {year}"
            records.append({
                "year": year,
                "ceremony": ceremony_name,
                "category": category,
                "nominee": nominee,
                "film": film,
                "country": "Germany",
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
    
    tables = soup.find_all("table", class_=re.compile("wikitable"))
    for table in tables:
        first_row = table.find("tr")
        if first_row:
            headers = [clean_text(th.get_text()).lower() for th in first_row.find_all("th")]
            if any(h in ["film", "actor", "actress", "director", "winner", "year"] for h in headers):
                records.extend(parse_bavarian_table(table, category, url))
            else:
                first_tds = [clean_text(th.get_text()) for th in first_row.find_all(["th", "td"])]
                if len(first_tds) >= 2 and re.search(r'\b(19|20)\d{2}\b', first_tds[0]):
                    records.extend(parse_bavarian_table(table, category, url))

    # Check all unordered lists
    for ul in soup.find_all("ul"):
        for li in ul.find_all("li"):
            li_text = clean_text(li.get_text())
            yr_m = re.match(r'^((?:19|20)\d{2})[\s:\-–]+(.*)', li_text)
            if yr_m:
                year = int(yr_m.group(1))
                rest = yr_m.group(2)
                film = ""
                nominee = ""

                if " for " in rest:
                    subparts = re.split(r'\s+for\s+', rest, maxsplit=1, flags=re.IGNORECASE)
                    nominee = subparts[0].strip()
                    film = subparts[1].strip()
                elif " - " in rest:
                    subparts = rest.split(" - ", 1)
                    nominee = subparts[0].strip()
                    film = subparts[1].strip()
                else:
                    nominee = rest

                if film or nominee:
                    if not film: film = nominee
                    ceremony_name = f"Bavarian Film Awards {year}"
                    records.append({
                        "year": year,
                        "ceremony": ceremony_name,
                        "category": category,
                        "nominee": nominee,
                        "film": film,
                        "country": "Germany",
                        "winner": 1,
                        "source_url": url
                    })

    return records

def main():
    print("[*] Starting Bavarian Film Awards scraping...")
    
    all_records = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_cat = {
            executor.submit(parse_page, url, cat, i % 5): cat
            for i, (cat, url) in enumerate(BAVARIAN_URLS.items())
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
        output_path = os.path.join(output_dir, "bavarian_awards.csv")
        df.to_csv(output_path, index=False, quoting=csv.QUOTE_MINIMAL)
        print(f"\n[+] Bavarian data saved: {output_path}")
        print(f"    Total unique records: {len(df)}")
        if len(df) > 0:
            print(f"    Years: {sorted(df['year'].unique())[:5]}...{sorted(df['year'].unique())[-5:]}")
    else:
        print("[-] No records scraped.")

if __name__ == "__main__":
    main()
