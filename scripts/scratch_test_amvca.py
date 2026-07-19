import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2023_Africa_Magic_Viewers%27_Choice_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\[[^\]]+\]', '', text)
    text = text.replace('†', '').replace('*', '').replace('‡', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_film_and_nominee(li_cell):
    i_tags = li_cell.find_all("i")
    if i_tags:
        film = clean_text(i_tags[0].get_text())
        li_copy = BeautifulSoup(str(li_cell), "lxml")
        for i_t in li_copy.find_all("i"):
            i_t.decompose()
        for sup in li_copy.find_all(["sup", "span"]):
            sup.decompose()
        remaining_text = clean_text(li_copy.get_text())
        # remove leading/trailing dashes and weird symbols
        nominee = re.sub(r'^[–\—\-\s\•\\–\—]+', '', remaining_text)
        nominee = re.sub(r'[–\—\-\s\•\\–\—]+$', '', nominee)
        nominee = clean_text(nominee)
        if not nominee:
            nominee = film
    else:
        text = clean_text(li_cell.get_text())
        parts = re.split(r'\s*[–\—\-]\s*', text)
        if len(parts) >= 2:
            film = parts[0]
            nominee = parts[1]
        else:
            film = text
            nominee = text
            
    return nominee, film

def is_winner_li(li_cell):
    if li_cell.find(["b", "strong"]):
        return True
    return False

def run_test():
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    
    tables = soup.find_all("table", class_=re.compile("wikitable"))
    if not tables:
        print("No tables found")
        return
        
    table = tables[0]
    rows = table.find_all("tr")
    print(f"Total rows: {len(rows)}")
    
    records = []
    current_categories = []
    
    for r_idx, row in enumerate(rows):
        th_cells = row.find_all("th")
        if th_cells:
            current_categories = [clean_text(th.get_text()) for th in th_cells]
            continue
            
        td_cells = row.find_all("td")
        if td_cells:
            for col_idx, td in enumerate(td_cells):
                if col_idx >= len(current_categories):
                    continue
                category = current_categories[col_idx]
                
                li_items = td.find_all("li")
                for li in li_items:
                    nominee, film = extract_film_and_nominee(li)
                    is_winner = is_winner_li(li)
                    
                    records.append({
                        "category": category,
                        "nominee": nominee,
                        "film": film,
                        "winner": 1 if is_winner else 0
                    })
                    
    print(f"Total records parsed: {len(records)}")
    print("First 10 records:")
    for r in records[:10]:
        print(" ", r)
        
run_test()
