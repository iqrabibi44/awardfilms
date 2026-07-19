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
    "User-Agent": "ItalianCinemaScraper/1.0 (educational data science project; contact: student_scraper@example.com)"
}

NASTRI_URLS = {
    "Best Director": "https://en.wikipedia.org/wiki/Nastro_d%27Argento_for_Best_Director",
    "Best Actor": "https://en.wikipedia.org/wiki/Nastro_d%27Argento_for_Best_Actor",
    "Best Actress": "https://en.wikipedia.org/wiki/Nastro_d%27Argento_for_Best_Actress",
    "Best Supporting Actor": "https://en.wikipedia.org/wiki/Nastro_d%27Argento_for_Best_Supporting_Actor",
    "Best Supporting Actress": "https://en.wikipedia.org/wiki/Nastro_d%27Argento_for_Best_Supporting_Actress",
    "Best Screenplay": "https://en.wikipedia.org/wiki/Nastro_d%27Argento_for_Best_Screenplay",
    "Best Score": "https://en.wikipedia.org/wiki/Nastro_d%27Argento_for_Best_Score"
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

def parse_nastri_list(html, category, source_url):
    soup = BeautifulSoup(html, "lxml")
    records = []
    
    # Check tables first just in case
    tables = soup.find_all("table", class_=re.compile("wikitable"))
    if tables:
        for table in tables:
            rows = table.find_all("tr")
            headers = []
            for row in rows:
                cells = row.find_all(["th", "td"])
                if not cells: continue
                if all(c.name == "th" for c in cells):
                    if len(cells) > 1:
                        headers = [clean_text(c.get_text()) for c in cells]
                    continue
                
                cell_texts = [clean_text(c.get_text()) for c in cells]
                if not any(cell_texts): continue

                is_winner = False
                row_style = row.get("style", "")
                if "background:#FAEB86" in row_style or "background:#B0C4DE" in row_style:
                    is_winner = True
                elif any(c.find(["b", "strong"]) for c in cells):
                    is_winner = True
                elif any("background" in c.get("style", "").lower() for c in cells if c.get("style")):
                    is_winner = True
                
                year = None
                nominee = ""
                film = ""

                # Very basic table extraction fallback for Nastri
                if len(cell_texts) >= 1:
                    yr_m = re.search(r'\b(19|20)\d{2}\b', cell_texts[0])
                    if yr_m:
                        year = int(yr_m.group())
                
                if not year: continue

                if len(cell_texts) >= 3:
                    nominee = cell_texts[1]
                    film = cell_texts[2]
                elif len(cell_texts) == 2:
                    nominee = cell_texts[1]
                
                if film or nominee:
                    if not film: film = nominee
                    ceremony_name = f"Nastri d'Argento {year}"
                    records.append({
                        "year": year,
                        "ceremony": ceremony_name,
                        "category": category,
                        "nominee": nominee,
                        "film": film,
                        "country": "Italy",
                        "winner": 1 if is_winner else 0,
                        "source_url": source_url
                    })
        if records:
            return records

    # List parsing if no table found
    headings = soup.find_all(["h2", "h3", "h4"])
    for heading in headings:
        heading_text = clean_text(heading.get_text())
        if "s" in heading_text and re.search(r'\b(19|20)\d{2}s\b', heading_text):
            # Decade heading
            start_elem = heading
            if heading.parent and heading.parent.name == "div" and any(
                cls.startswith("mw-heading") for cls in heading.parent.get("class", [])
            ):
                start_elem = heading.parent

            sibling = start_elem.next_sibling
            while sibling:
                sname = getattr(sibling, 'name', None)
                if sname in ("h2", "h3") or (sname == "div" and any(cls.startswith("mw-heading") for cls in sibling.get("class", []))):
                    break
                    
                if sname == "ul":
                    for li in sibling.find_all("li"):
                        li_text = clean_text(li.get_text())
                        # Expected format: "1990 - Name - Film" or "1990: Name - Film" or "1990 Name for Film"
                        yr_m = re.match(r'^((?:19|20)\d{2})[\s:\-–]+(.*)', li_text)
                        if yr_m:
                            year = int(yr_m.group(1))
                            rest = yr_m.group(2)
                            film = ""
                            nominee = ""

                            if " - " in rest:
                                subparts = rest.split(" - ", 1)
                                nominee = subparts[0].strip()
                                film = subparts[1].strip()
                            elif " – " in rest:
                                subparts = rest.split(" – ", 1)
                                nominee = subparts[0].strip()
                                film = subparts[1].strip()
                            elif " for " in rest:
                                subparts = re.split(r'\s+for\s+', rest, maxsplit=1, flags=re.IGNORECASE)
                                nominee = subparts[0].strip()
                                film = subparts[1].strip()
                            else:
                                nominee = rest

                            if film or nominee:
                                if not film: film = nominee
                                ceremony_name = f"Nastri d'Argento {year}"
                                records.append({
                                    "year": year,
                                    "ceremony": ceremony_name,
                                    "category": category,
                                    "nominee": nominee,
                                    "film": film,
                                    "country": "Italy",
                                    "winner": 1, # List usually only shows winners
                                    "source_url": source_url
                                })
                sibling = sibling.next_sibling

    return records

def parse_page(url, category, thread_id):
    proxies = get_proxies(thread_id)
    html = fetch_page(url, proxies)
    if not html:
        return []

    return parse_nastri_list(html, category, url)

def main():
    print("[*] Starting Nastri d'Argento scraping...")
    
    all_records = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_cat = {
            executor.submit(parse_page, url, cat, i % 5): cat
            for i, (cat, url) in enumerate(NASTRI_URLS.items())
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
        output_path = os.path.join(output_dir, "nastri_awards.csv")
        df.to_csv(output_path, index=False, quoting=csv.QUOTE_MINIMAL)
        print(f"\n[+] Nastri data saved: {output_path}")
        print(f"    Total unique records: {len(df)}")
        if len(df) > 0:
            print(f"    Years: {sorted(df['year'].unique())[:5]}...{sorted(df['year'].unique())[-5:]}")
    else:
        print("[-] No records scraped.")

if __name__ == "__main__":
    main()
