import requests
from bs4 import BeautifulSoup
import re

def clean_text(text):
    if not isinstance(text, str):
        return ""
    # Remove citations [1], [a], etc.
    text = re.sub(r'\[[^\]]+\]', '', text)
    # Remove newlines and weird spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_year(text):
    match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
    if match:
        return int(match.group(1))
    return None

def is_winner_cell(cell, row):
    # Check if the cell or its row has a background color indicating a winner
    style = cell.get('style', '').lower()
    row_style = row.get('style', '').lower()
    
    if 'background' in style or 'background' in row_style:
        if 'transparent' not in style and 'none' not in style and 'transparent' not in row_style and 'none' not in row_style:
            return True
    
    # Check if the text contains a star or dagger which might indicate a winner
    text = cell.get_text()
    if '‡' in text or '*' in text:
        return True
        
    return False

def fetch_and_parse_wiki(wiki_slug, category_name, canon_category, founded_year):
    url = f"https://en.wikipedia.org/wiki/{wiki_slug}"
    records = []
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code != 200:
            print(f"Warning: Failed to fetch {url}")
            return []
        
        soup = BeautifulSoup(r.text, 'lxml')
        for sup in soup.find_all('sup'):
            sup.decompose()
            
        tables = soup.find_all('table', class_='wikitable')
        
        for table in tables:
            current_year = None
            rowspans = {}
            
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if not cells:
                    continue
                
                # Check for year in the first cell
                first_text = cells[0].get_text(strip=True)
                possible_year = extract_year(first_text)
                
                if possible_year:
                    current_year = possible_year
                    if 'rowspan' in cells[0].attrs:
                        try:
                            span = int(cells[0]['rowspan'])
                            rowspans['year'] = {'value': current_year, 'remaining': span - 1}
                        except ValueError:
                            pass
                    cells = cells[1:]
                elif 'year' in rowspans and rowspans['year']['remaining'] > 0:
                    current_year = rowspans['year']['value']
                    rowspans['year']['remaining'] -= 1
                else:
                    # Look for year in headers
                    if cells[0].name == 'th':
                        possible_year = extract_year(first_text)
                        if possible_year:
                            current_year = possible_year
                            cells = cells[1:]
                
                if not cells or not current_year:
                    continue
                
                # Assume 1st remaining cell is Nominee/Film, 2nd is the other
                # Determine winner based on styling
                winner = is_winner_cell(cells[0], row)
                
                name = clean_text(cells[0].get_text())
                film = clean_text(cells[1].get_text()) if len(cells) > 1 else ""
                
                # If "Best Film", flip name and film since the first column is usually the Film title
                if 'film' in category_name.lower():
                    temp = name
                    name = film
                    film = temp
                
                # Skip header rows
                if 'recipient' in name.lower() or 'nominee' in name.lower() or 'film' in film.lower():
                    continue
                if name.lower() == 'no other nominees' or film.lower() == 'no other nominees':
                    continue
                    
                if not name and not film:
                    continue
                    
                year_ceremony = current_year + 1
                ceremony_idx = current_year - founded_year + 1
                
                records.append({
                    "year_film": current_year,
                    "year_ceremony": year_ceremony,
                    "ceremony": max(1, ceremony_idx),
                    "category": category_name,
                    "canon_category": canon_category,
                    "name": name,
                    "film": film,
                    "winner": winner
                })

    except Exception as e:
        print(f"Error parsing {url}: {e}")
        
    return records
