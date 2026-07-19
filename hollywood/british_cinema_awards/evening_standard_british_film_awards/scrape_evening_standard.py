import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
import random

TOR_SOCKS_PORT = 9050
HEADERS = {
    "User-Agent": "BritishCinemaScraper/1.0 (educational data science project; contact: student_scraper@example.com)"
}

URL = "https://en.wikipedia.org/wiki/Evening_Standard_British_Film_Awards"

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

def parse_evening_standard(html, source_url):
    soup = BeautifulSoup(html, "lxml")
    records = []
    
    headings = soup.find_all(["h2", "h3", "h4"])
    for heading in headings:
        heading_text = clean_text(heading.get_text())
        year_match = re.search(r'\b(19|20)\d{2}\b', heading_text)
        if not year_match or "winner" not in heading_text.lower() or "–" in heading_text or "-" in heading_text:
            continue
            
        year = int(year_match.group())
        ceremony_name = f"Evening Standard British Film Awards {year}"
        
        start_elem = heading
        if heading.parent and heading.parent.name == "div" and any(
            cls.startswith("mw-heading") for cls in heading.parent.get("class", [])
        ):
            start_elem = heading.parent

        sibling = start_elem.next_sibling
        count = 0
        while sibling and count < 10:
            sname = getattr(sibling, 'name', None)
            if sname in ("h2", "h3", "h4"):
                break
            if sname == "div" and any(cls.startswith("mw-heading") for cls in sibling.get("class", [])):
                break
                
            if sname == "ul":
                for li in sibling.find_all("li"):
                    li_text = clean_text(li.get_text())
                    if not li_text or ":" not in li_text:
                        continue
                        
                    parts = li_text.split(":", 1)
                    if len(parts) == 2:
                        category = parts[0].strip()
                        rest = parts[1].strip()
                        
                        film = ""
                        nominee = ""
                        
                        # Handle specific formats
                        if "Best Actor" in category or "Best Actress" in category:
                            # Usually: "Name - Film" or "Name for Film"
                            if " for " in rest.lower():
                                subparts = re.split(r'\s+for\s+', rest, maxsplit=1, flags=re.IGNORECASE)
                                nominee = subparts[0].strip()
                                film = subparts[1].strip()
                            elif " - " in rest:
                                subparts = rest.split(" - ", 1)
                                nominee = subparts[0].strip()
                                film = subparts[1].strip()
                            else:
                                nominee = rest
                        else:
                            # Usually "Film - Director"
                            if " - " in rest:
                                subparts = rest.split(" - ", 1)
                                film = subparts[0].strip()
                                nominee = subparts[1].strip()
                            else:
                                film = rest
                                
                        if film or nominee:
                            records.append({
                                "year": year,
                                "ceremony": ceremony_name,
                                "category": category,
                                "nominee": nominee,
                                "film": film,
                                "country": "UK",
                                "winner": 1,
                                "source_url": source_url
                            })
            count += 1
            sibling = sibling.next_sibling
            
    return records

def main():
    print("[*] Starting Evening Standard British Film Awards scraping...")
    proxies = get_proxies()
    html = fetch_page(URL, proxies)
    
    if html:
        records = parse_evening_standard(html, URL)
        print(f"[+] Parsed {len(records)} records.")
        
        df = pd.DataFrame(records)
        if not df.empty:
            df = df.drop_duplicates(subset=["year", "category", "nominee", "film"])
            df = df.sort_values(by=["year", "category", "winner", "nominee"], ascending=[True, True, False, True])

            import csv
            output_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(output_dir, "evening_standard_awards.csv")
            df.to_csv(output_path, index=False, quoting=csv.QUOTE_MINIMAL)
            print(f"\n[+] Evening Standard data saved: {output_path}")
            print(f"    Total unique records: {len(df)}")
            print(f"    Years: {sorted(df['year'].unique())[:5]}...{sorted(df['year'].unique())[-5:]}")
        else:
            print("[-] No records scraped.")
    else:
        print("[-] Failed to fetch main page.")

if __name__ == "__main__":
    main()
