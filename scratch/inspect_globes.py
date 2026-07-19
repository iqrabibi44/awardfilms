import requests
from bs4 import BeautifulSoup
import re

def clean_text(text):
    text = re.sub(r'\[[^\]]+\]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def parse_nominee_li(li, is_winner=False):
    # Usually format is: "WinnerName - FilmName as Character"
    # or just "FilmName"
    # Bold text is usually the winner, but we rely on first item = winner
    text = clean_text(li.get_text())
    # Try to split by ' – ' or ' - '
    parts = re.split(r' \– | \- | \— ', text, 1)
    nominee = parts[0].strip()
    film = parts[1].strip() if len(parts) > 1 else ""
    
    # Remove roles like "as J. Robert Oppenheimer"
    film = re.sub(r' as .*$', '', film).strip()
    return nominee, film

def parse_page(url, year):
    print(f"\nParsing {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.content, 'lxml')
    
    records = []
    
    # Method 1: Wikitables
    tables = soup.find_all('table', class_='wikitable')
    for table in tables:
        # Check if this table has categories (ignore stats tables)
        header_text = table.get_text().lower()
        if 'nominations' in header_text and 'distributor' in header_text:
            continue # stats table
            
        cells = table.find_all(['td', 'th'])
        for cell in cells:
            category_elem = cell.find('b') or cell.find('div')
            if not category_elem:
                continue
            category = clean_text(category_elem.get_text())
            if not category or 'best' not in category.lower():
                continue
                
            ul = cell.find('ul')
            if not ul:
                continue
                
            lis = ul.find_all('li', recursive=False)
            for i, li in enumerate(lis):
                is_winner = (i == 0)
                nominee, film = parse_nominee_li(li, is_winner)
                records.append({
                    'year': year, 'category': category, 
                    'nominee': nominee, 'film': film, 'winner': 1 if is_winner else 0
                })

    # Method 2: Header + UL (For older pages like 1st Golden Globes)
    if not records:
        print("Using Method 2 for", url)
        # Find all h2, h3, h4, or b that might precede a ul
        for header in soup.find_all(['h2', 'h3', 'h4', 'dt']):
            category = clean_text(header.get_text())
            if 'best' not in category.lower() and 'award' not in category.lower():
                continue
            
            ul = header.find_next_sibling(['ul', 'dl'])
            if not ul:
                continue
                
            lis = ul.find_all(['li', 'dd'], recursive=False)
            for i, li in enumerate(lis):
                is_winner = (i == 0) or ('winner' in li.get_text().lower() and len(lis) == 1)
                # Older lists might just have 1 winner
                nominee, film = parse_nominee_li(li, is_winner)
                records.append({
                    'year': year, 'category': category, 
                    'nominee': nominee, 'film': film, 'winner': 1 if is_winner else 0
                })
                
    print(f"Found {len(records)} records")
    for r in records[:3]:
        print(r)

parse_page("https://en.wikipedia.org/wiki/81st_Golden_Globe_Awards", 2023)
parse_page("https://en.wikipedia.org/wiki/1st_Golden_Globe_Awards", 1943)
parse_page("https://en.wikipedia.org/wiki/2nd_Golden_Globe_Awards", 1944)
