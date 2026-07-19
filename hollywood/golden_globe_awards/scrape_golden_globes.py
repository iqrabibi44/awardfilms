import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
import time

URL = "https://en.wikipedia.org/wiki/List_of_Golden_Globe_Awards_ceremonies"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\[[^\]]+\]', '', text)
    text = text.replace('†', '').replace('*', '').replace('‡', '').replace('§', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_nominee(text):
    text = clean_text(text)
    # Split by common dash formats.
    # Often: "PersonName – FilmName as Role" or "FilmName"
    parts = re.split(r' \– | \- | \— | \: ', text, 1)
    nominee = parts[0].strip()
    film = parts[1].strip() if len(parts) > 1 else ""
    
    # Remove roles like "as Character"
    film = re.sub(r' as .*$', '', film).strip()
    # Or sometimes nominee has "as Character"
    nominee = re.sub(r' as .*$', '', nominee).strip()
    
    # If no film was found by split, but there are quotes, maybe film is in quotes
    if not film and '"' in nominee:
        match = re.search(r'"([^"]+)"', nominee)
        if match:
            film = match.group(1)
            nominee = nominee.replace(f'"{film}"', '').strip()
            
    if not film:
        # Golden Globes sometimes just lists the Film Name for Best Picture
        film = nominee
        nominee = nominee
        
    return nominee, film

def extract_lists_from_ul(ul):
    results = []
    # Check if first li has a nested ul
    first_li = ul.find('li', recursive=False)
    if not first_li:
        return results
        
    nested_ul = first_li.find(['ul', 'dl'], recursive=False)
    if nested_ul:
        # Nested format
        # Winner is first_li text without nested_ul
        clone = BeautifulSoup(str(first_li), 'lxml').find('li')
        if clone.find(['ul', 'dl']):
            clone.find(['ul', 'dl']).decompose()
        winner_text = clone.get_text()
        results.append((winner_text, True))
        
        for n_li in nested_ul.find_all('li', recursive=False):
            results.append((n_li.get_text(), False))
    else:
        # Flat format
        lis = ul.find_all('li', recursive=False)
        for i, li in enumerate(lis):
            is_winner = (i == 0) or bool(li.find('b'))
            results.append((li.get_text(), is_winner))
            
    return results

def scrape_ceremony(url, year, ceremony_name):
    print(f"Scraping {ceremony_name} ({year})...")
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'lxml')
    records = []
    
    # We will find all ul elements that might contain nominees.
    # To avoid navboxes and references, we only look inside the main content.
    content = soup.find('div', class_='mw-parser-output')
    if not content:
        content = soup
        
    for ul in content.find_all(['ul', 'dl']):
        # Ignore reference lists or navbox lists
        if ul.find_parent('div', class_=['navbox', 'reflist', 'references']):
            continue
            
        # Check if this ul contains nominees. Usually the first li has bold text or just text
        first_li = ul.find('li')
        if not first_li:
            continue
            
        # Try to find the category for this ul
        category = None
        
        # 1. Check if the cell/parent contains a bold or div BEFORE the ul
        parent_td = ul.find_parent('td')
        if parent_td:
            # Look for b or div in the same td
            for cat_elem in parent_td.find_all(['b', 'div']):
                if cat_elem.sourceline is not None and ul.sourceline is not None and cat_elem.sourceline <= ul.sourceline:
                    text = clean_text(cat_elem.get_text())
                    if any(w in text.lower() for w in ['best', 'award', 'picture', 'actor', 'actress', 'director', 'screenplay', 'score', 'song', 'animated', 'drama', 'comedy', 'musical']):
                        category = text
                        break
                elif cat_elem.sourceline is None or ul.sourceline is None:
                    # Fallback if sourceline is missing
                    text = clean_text(cat_elem.get_text())
                    if any(w in text.lower() for w in ['best', 'award', 'picture', 'actor', 'actress', 'director', 'screenplay', 'score', 'song', 'animated', 'drama', 'comedy', 'musical']):
                        category = text
                        break
        
        # 2. If not found in same td, look for preceding th, h2, h3, h4
        if not category:
            prev = ul.find_previous(['th', 'h2', 'h3', 'h4', 'dt'])
            while prev:
                # Ensure it's not too far up
                if prev.name in ['h2', 'h3'] or (parent_td and prev.name == 'th'):
                    text = clean_text(prev.get_text())
                    if any(w in text.lower() for w in ['best', 'award', 'picture', 'actor', 'actress', 'director', 'screenplay', 'score', 'song', 'animated', 'drama', 'comedy', 'musical']):
                        category = text
                        
                        # Sometimes th just says "Drama". We should look at the th above it to get "Best Motion Picture"
                        if prev.name == 'th' and len(text) < 15:
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
            if not nom or len(nom) > 100: # skip garbage
                continue
            records.append({
                'year': year, 'ceremony': ceremony_name,
                'category': category, 'nominee': nom, 'film': film,
                'winner': 1 if is_winner else 0, 'source_url': url
            })
            
    return records

def main():
    from urllib.parse import urljoin
    print("Fetching list of ceremonies...")
    
    # Configure Tor Proxy
    TOR_SOCKS_PORT = 9050
    proxies = {
        "http": f"socks5h://thread_globe:secret@127.0.0.1:{TOR_SOCKS_PORT}",
        "https": f"socks5h://thread_globe:secret@127.0.0.1:{TOR_SOCKS_PORT}",
    }
    
    # Update HEADERS with proxies globally for the requests in scrape_ceremony
    global HEADERS
    
    try:
        resp = requests.get(URL, headers=HEADERS, proxies=proxies)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch list of ceremonies via Tor: {e}")
        # fallback to no proxy if needed
        resp = requests.get(URL, headers=HEADERS)
        proxies = None # clear so scrape_ceremony doesn't use it if it failed
        
    soup = BeautifulSoup(resp.content, 'lxml')
    
    main_table = soup.find('table', class_='wikitable')
    ceremony_links = []
    
    for row in main_table.find_all('tr')[1:]:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 3:
            a = cells[0].find('a')
            if a and 'Golden_Globe' in a.get('href', ''):
                href = urljoin("https://en.wikipedia.org", a['href'])
                ceremony_name = clean_text(a.get_text()) + " Golden Globe Awards"
                year_text = clean_text(cells[2].get_text())
                year_match = re.search(r'(19|20)\d{2}', year_text)
                if year_match:
                    year = int(year_match.group(0))
                    ceremony_links.append((href, year, ceremony_name))
                    
    print(f"Found {len(ceremony_links)} ceremonies.")
    
    all_records = []
    for link, year, name in ceremony_links:
        try:
            records = scrape_ceremony(link, year, name)
            print(f"  -> Found {len(records)} records.")
            all_records.extend(records)
            time.sleep(0.5)
        except Exception as e:
            print(f"Error scraping {link}: {e}")
            
    df = pd.DataFrame(all_records)
    if not df.empty:
        df = df.drop_duplicates(subset=["year", "category", "nominee", "film"])
        out_dir = os.path.dirname(os.path.abspath(__file__))
        out_file = os.path.join(out_dir, "golden_globe_awards.csv")
        df.to_csv(out_file, index=False)
        print(f"Saved {len(df)} records to {out_file}")
    else:
        print("No records scraped!")

if __name__ == "__main__":
    main()
