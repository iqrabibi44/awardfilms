import os
import sys
import re
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

URL = "https://en.wikipedia.org/wiki/Screen_Actors_Guild_Awards"

HEADERS = {"User-Agent": "Mozilla/5.0"}

def clean_text(text):
    if not text: return ""
    text = re.sub(r'\[.*?\]', '', text)
    text = text.replace('\xa0', ' ').replace('\n', ' ')
    return text.strip()

def parse_nominee(text):
    parts = text.split(' – ', 1)
    if len(parts) == 1:
        parts = text.split(' - ', 1)
        
    if len(parts) == 2:
        nominee = parts[0].strip()
        film = parts[1].strip()
        
        match = re.match(r'^(.*?)\s+as\s+(.*)$', film, flags=re.IGNORECASE)
        if match:
            film = match.group(1).strip()
            
        return nominee, film
        
    return text.strip(), ""

def extract_lists_from_ul(ul):
    results = []
    first_li = ul.find('li', recursive=False)
    if not first_li:
        return results
        
    nested_ul = first_li.find(['ul', 'dl'], recursive=False)
    if nested_ul:
        clone = BeautifulSoup(str(first_li), 'lxml').find('li')
        if clone.find(['ul', 'dl']):
            clone.find(['ul', 'dl']).decompose()
        winner_text = clone.get_text()
        results.append((winner_text, True))
        
        for n_li in nested_ul.find_all('li', recursive=False):
            results.append((n_li.get_text(), False))
    else:
        lis = ul.find_all('li', recursive=False)
        for i, li in enumerate(lis):
            is_winner = (i == 0) or bool(li.find('b'))
            results.append((li.get_text(), is_winner))
            
    return results

def scrape_ceremony(url, year, ceremony_name, proxies):
    print(f"Scraping {ceremony_name} ({year})...")
    try:
        resp = requests.get(url, headers=HEADERS, proxies=proxies, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []
        
    soup = BeautifulSoup(resp.content, 'lxml')
    records = []
    
    content = soup.find('div', class_='mw-parser-output')
    if not content:
        content = soup
        
    for ul in content.find_all(['ul', 'dl']):
        if ul.find_parent('div', class_=['navbox', 'reflist', 'references']):
            continue
            
        first_li = ul.find('li')
        if not first_li:
            continue
            
        category = None
        
        parent_td = ul.find_parent('td')
        if parent_td:
            for cat_elem in parent_td.find_all(['b', 'div', 'th']):
                if cat_elem.sourceline is not None and ul.sourceline is not None and cat_elem.sourceline <= ul.sourceline:
                    text = clean_text(cat_elem.get_text())
                    if any(w in text.lower() for w in ['best', 'outstanding', 'award', 'performance', 'actor', 'actress', 'cast', 'ensemble', 'stunt']):
                        category = text
                        break
                elif cat_elem.sourceline is None or ul.sourceline is None:
                    text = clean_text(cat_elem.get_text())
                    if any(w in text.lower() for w in ['best', 'outstanding', 'award', 'performance', 'actor', 'actress', 'cast', 'ensemble', 'stunt']):
                        category = text
                        break
        
        if not category:
            prev = ul.find_previous(['th', 'h2', 'h3', 'h4', 'dt'])
            while prev:
                if prev.name in ['h2', 'h3'] or (parent_td and prev.name == 'th'):
                    text = clean_text(prev.get_text())
                    if any(w in text.lower() for w in ['best', 'outstanding', 'award', 'performance', 'actor', 'actress', 'cast', 'ensemble', 'stunt']):
                        category = text
                        
                        if prev.name == 'th' and len(text) < 25:
                            prev_th = prev.find_previous('th')
                            if prev_th:
                                category = clean_text(prev_th.get_text()) + " - " + text
                        break
                prev = prev.find_previous(['th', 'h2', 'h3', 'h4', 'dt'])
                
        if not category:
            continue
            
        items = extract_lists_from_ul(ul)
        for text, is_winner in items:
            nom, film = parse_nominee(text)
            if not nom or len(nom) > 150:
                continue
            records.append({
                'year': year, 'ceremony': ceremony_name,
                'category': category, 'nominee': nom, 'film': film,
                'winner': 1 if is_winner else 0, 'source_url': url
            })
            
    return records

def main():
    print("Fetching list of ceremonies...")
    
    TOR_SOCKS_PORT = 9050
    proxies = {
        "http": f"socks5h://thread_sag:secret@127.0.0.1:{TOR_SOCKS_PORT}",
        "https": f"socks5h://thread_sag:secret@127.0.0.1:{TOR_SOCKS_PORT}",
    }
    
    global HEADERS
    
    try:
        resp = requests.get(URL, headers=HEADERS, proxies=proxies, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch list of ceremonies via Tor: {e}")
        resp = requests.get(URL, headers=HEADERS)
        proxies = None
        
    soup = BeautifulSoup(resp.content, 'lxml')
    
    ceremony_links = []
    for a in soup.find_all('a', href=re.compile(r'/wiki/\d+(st|nd|rd|th)_Screen_Actors_Guild_Awards')):
        href = urljoin("https://en.wikipedia.org", a['href'])
        ceremony_name = clean_text(a.get_text())
        
        # ensure it's not a reference/citation
        if '[' in ceremony_name or not ceremony_name.strip():
            continue
            
        # extract year from ceremony name (e.g., 30th Screen Actors Guild Awards -> usually we want the FILM year)
        # However, it's easier to just pull the film year from the title if available, or just use the ceremony iteration.
        # Actually, let's find the film year by matching \d{4} in the row or just falling back to 1993+iteration
        year_match = re.search(r'(\d+)(st|nd|rd|th)', ceremony_name)
        if year_match:
            iteration = int(year_match.group(1))
            year = 1993 + iteration # 1st SAG Awards honored films of 1994, actually 1st SAG Awards was in 1995 for 1994 films.
            # So year = 1993 + iteration -> 1st = 1994, 2nd = 1995, 30th = 2023.
            ceremony_links.append((href, year, ceremony_name))
            
    # Remove duplicates but keep order
    seen = set()
    unique_links = []
    for link, year, name in ceremony_links:
        if link not in seen:
            seen.add(link)
            unique_links.append((link, year, name))
            
    print(f"Found {len(unique_links)} ceremonies.")
    
    all_records = []
    
    # Load existing CSV to skip completed years
    existing_years = set()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_file = os.path.join(out_dir, "screen_actors_guild_awards.csv")
    if os.path.exists(out_file):
        try:
            df_existing = pd.read_csv(out_file)
            existing_years = set(df_existing['year'].unique())
            print(f"Found existing CSV with years: sorted(list({existing_years}))")
            # We will append to it later
            all_records = df_existing.to_dict('records')
        except Exception as e:
            print("Could not read existing CSV:", e)

    for link, year, name in unique_links:
        if year in existing_years:
            print(f"Skipping {name} ({year}) as it is already scraped.")
            continue
            
        try:
            records = scrape_ceremony(link, year, name, None)
            print(f"  -> Found {len(records)} records.")
            all_records.extend(records)
            time.sleep(3) # Increase sleep to avoid rate limits
        except Exception as e:
            print(f"Error scraping {link}: {e}")
            
    df = pd.DataFrame(all_records)
    if not df.empty:
        df = df.drop_duplicates(subset=["year", "category", "nominee", "film"])
        out_dir = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, "screen_actors_guild_awards.csv")
        df.to_csv(out_file, index=False)
        print(f"Saved {len(df)} records to {out_file}")
    else:
        print("No records scraped!")

if __name__ == "__main__":
    main()
