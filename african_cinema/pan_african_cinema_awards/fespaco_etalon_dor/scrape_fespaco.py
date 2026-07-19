import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
import random

TOR_SOCKS_PORT = 9050
HEADERS = {
    "User-Agent": "PanAfricanCinemaScraper/1.0 (educational data science project; contact: student_scraper@example.com)"
}

FESPACO_MAIN_URL = "https://en.wikipedia.org/wiki/List_of_FESPACO_award_winners"

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
                print(f"    Failed to fetch {url}: {e}")
            time.sleep(random.uniform(1.0, 3.0))
    return None

def parse_li_item(li_text, year, ceremony_name, source_url):
    """
    Parse a FESPACO list item like:
    'First prize (Étalon de Yennenga): Baara by Souleymane Cissé (Mali).'
    'Best Actor: Alassane Sy in Baamum Nafi by Mamadou Dia (Senegal)'
    """
    li_text = clean_text(li_text)
    if not li_text or len(li_text) < 5:
        return None

    # Split on first ':' to get category vs rest
    colon_idx = li_text.find(':')
    if colon_idx == -1:
        return None

    category = clean_text(li_text[:colon_idx])
    rest = clean_text(li_text[colon_idx + 1:])

    if not category or not rest:
        return None

    # Category must be a short award name, not a sentence
    if len(category) > 80 or len(category.split()) > 10:
        return None

    # Skip non-award lines (e.g. info sentences)
    skip_keywords = ["films were shown", "selection included", "festival was", "countries", "included among"]
    if any(kw in category.lower() for kw in skip_keywords):
        return None
    if any(kw in rest.lower()[:50] for kw in ["films were shown", "countries", "festival was"]):
        return None

    # Check for " in " pattern (e.g. Best Actor: Name in Film by Director)
    nominee = ""
    in_pattern = re.split(r'\s+in\s+', rest, maxsplit=1, flags=re.IGNORECASE)
    if len(in_pattern) == 2 and any(k in category.lower() for k in ["actor", "actress"]):
        nominee = clean_text(in_pattern[0])
        rest = clean_text(in_pattern[1])

    # Split on ' by ' to get film and director
    by_pattern = re.split(r'\s+by\s+', rest, maxsplit=1, flags=re.IGNORECASE)
    if len(by_pattern) == 2:
        film = clean_text(by_pattern[0])
        director_part = clean_text(by_pattern[1])
        # Extract country from trailing parentheses
        country_match = re.search(r'\(([^)]+)\)\s*\.?\s*$', director_part)
        country = clean_text(country_match.group(1)) if country_match else ""
        director = clean_text(re.sub(r'\s*\([^)]+\)\s*\.?\s*$', '', director_part))
        if not nominee:
            nominee = director
    else:
        film = rest.rstrip('.')
        country = ""
        director = ""

    # Film must be reasonably short
    if len(film) > 200:
        return None

    # Determine winner
    is_winner = True  # Wikipedia FESPACO list only contains winners

    return {
        "year": year,
        "ceremony": ceremony_name,
        "category": category,
        "nominee": nominee,
        "film": film,
        "country": country,
        "winner": 1 if is_winner else 0,
        "source_url": source_url
    }


def parse_fespaco_page(html, source_url):
    soup = BeautifulSoup(html, "lxml")
    records = []

    headings = soup.find_all(["h2", "h3", "h4"])
    for heading in headings:
        heading_text = clean_text(heading.get_text())

        # Skip non-year headings
        year_match = re.search(r'\b(19|20)\d{2}\b', heading_text)
        if not year_match:
            continue

        year = int(year_match.group())
        ceremony_name = f"FESPACO {year}"

        # Handle mw-heading wrappers
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

            # Stop at next heading
            if sname in ("h2", "h3", "h4"):
                break
            if sname == "div" and any(
                cls.startswith("mw-heading") for cls in sibling.get("class", [])
            ):
                break

            # Parse list items
            if sname in ("ul", "ol"):
                for li in sibling.find_all(["li"], recursive=False):
                    li_text = clean_text(li.get_text())
                    rec = parse_li_item(li_text, year, ceremony_name, source_url)
                    if rec:
                        records.append(rec)
                    # Also handle nested list items
                    for nested_li in li.find_all("li"):
                        nested_text = clean_text(nested_li.get_text())
                        nested_rec = parse_li_item(nested_text, year, ceremony_name, source_url)
                        if nested_rec:
                            records.append(nested_rec)

            # Parse definition lists (dl/dt/dd)
            elif sname == "dl":
                for dt in sibling.find_all("dt"):
                    category = clean_text(dt.get_text())
                    for dd in dt.find_next_siblings("dd"):
                        if dd.parent != sibling:
                            break
                        dd_text = clean_text(dd.get_text())
                        by_parts = re.split(r'\s+by\s+', dd_text, maxsplit=1, flags=re.IGNORECASE)
                        film = clean_text(by_parts[0]) if by_parts else dd_text
                        director = clean_text(by_parts[1]) if len(by_parts) > 1 else ""
                        country_m = re.search(r'\(([^)]+)\)\s*\.?\s*$', director)
                        country = clean_text(country_m.group(1)) if country_m else ""
                        director = clean_text(re.sub(r'\s*\([^)]+\)\s*\.?\s*$', '', director))
                        is_winner = bool(re.search(r'(first prize|étalon)', category, re.IGNORECASE))
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

            # Parse paragraphs containing award text
            elif sname == "p":
                p_text = clean_text(sibling.get_text())
                if ':' in p_text and len(p_text) > 10:
                    # Try splitting into individual awards by sentence
                    sentences = re.split(r'\.\s+(?=[A-Z])', p_text)
                    for sent in sentences:
                        rec = parse_li_item(sent, year, ceremony_name, source_url)
                        if rec:
                            records.append(rec)

            sibling = sibling.next_sibling

    return records

def main():
    print("[*] Starting FESPACO scraping run...")
    proxies = get_proxies(0)

    try:
        ip = requests.get("https://icanhazip.com", proxies=proxies, timeout=15).text.strip()
        print(f"[*] Tor IP: {ip}")
    except Exception:
        pass

    html = fetch_page(FESPACO_MAIN_URL, proxies)
    if not html:
        print("[-] Failed to fetch FESPACO page.")
        return

    records = parse_fespaco_page(html, FESPACO_MAIN_URL)
    print(f"[*] Parsed {len(records)} raw records.")

    df = pd.DataFrame(records)
    if not df.empty:
        df = df.drop_duplicates(subset=["year", "category", "nominee", "film"])
        df = df.sort_values(by=["year", "category", "winner", "nominee"], ascending=[True, True, False, True])

        import csv
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(output_dir, "fespaco_awards.csv")
        df.to_csv(output_path, index=False, quoting=csv.QUOTE_MINIMAL)
        print(f"[+] FESPACO data saved to: {output_path}")
        print(f"    Total unique records: {len(df)}")
        print(f"    Years covered: {sorted(df['year'].unique())}")
    else:
        print("[-] No records scraped for FESPACO.")

if __name__ == "__main__":
    main()
