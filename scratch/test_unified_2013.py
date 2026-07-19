import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2013_Africa_Magic_Viewers%27_Choice_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\[[^\]]+\]', '', text)
    text = text.replace('†', '').replace('*', '').replace('‡', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_film_and_nominee(li_cell):
    li_copy = BeautifulSoup(str(li_cell), "lxml").find("li")
    if not li_copy:
        li_copy = li_cell
        
    for nested in li_copy.find_all(["ul", "ol"]):
        nested.decompose()
    for tag in li_copy.find_all(["sup", "span"]):
        tag.decompose()
        
    i_tags = li_copy.find_all("i")
    if i_tags:
        film_candidate = clean_text(i_tags[0].get_text())
        for i_t in li_copy.find_all("i"):
            i_t.decompose()
        rest_candidate = clean_text(li_copy.get_text())
        
        film = film_candidate
        nominee = rest_candidate
        
        if not nominee:
            parts = re.split(r'\s*[–\—\-]\s*', film)
            if len(parts) >= 2:
                film = parts[0]
                nominee = parts[1]
            else:
                nominee = film
        else:
            nominee = re.sub(r'^[–\—\-\s\•\\–\—]+', '', nominee)
            nominee = re.sub(r'[–\—\-\s\•\\–\—]+$', '', nominee)
            nominee = clean_text(nominee)
    else:
        text = clean_text(li_copy.get_text())
        parts = re.split(r'\s*[–\—\-]\s*', text)
        if len(parts) >= 2:
            film = parts[0]
            nominee = parts[1]
        else:
            film = text
            nominee = text
            
    return clean_text(nominee), clean_text(film)

def is_winner_li(li_cell):
    if li_cell.find(["b", "strong"]):
        return True
    return False

def parse_ceremony_page(html, ceremony_name, year, source_url):
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table", class_=re.compile("wikitable"))
    
    records = []
    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue
            
        current_categories = []
        for row in rows:
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
                
            # Layout 1: Heading Row Sets Category
            if all(cell.name == "th" for cell in cells):
                current_categories = [clean_text(cell.get_text()) for cell in cells]
                continue
                
            for col_idx, cell in enumerate(cells):
                category = None
                first_ul = cell.find("ul")
                if first_ul:
                    cell_text = cell.get_text()
                    ul_text = first_ul.get_text()
                    if ul_text in cell_text:
                        prefix = cell_text.split(ul_text)[0]
                        prefix_clean = clean_text(prefix)
                        if prefix_clean and len(prefix_clean) < 120 and prefix_clean.lower() not in ("winner", "nominees", "result", "category"):
                            category = prefix_clean
                            
                # Fallback to Layout 2
                if not category and len(cells) == 2:
                    li_items_0 = cells[0].find_all("li")
                    li_items_1 = cells[1].find_all("li")
                    if li_items_1 and not li_items_0:
                        cat_text = clean_text(cells[0].get_text())
                        if cat_text and len(cat_text) < 120 and cat_text.lower() not in ("winner", "nominees", "result", "category"):
                            if col_idx == 1:
                                category = cat_text
                                cell = cells[1]
                                first_ul = cell.find("ul")
                                
                # Fallback to Layout 1
                if not category and current_categories and col_idx < len(current_categories):
                    cat_text = current_categories[col_idx]
                    if cat_text and cat_text.lower() not in ("winner", "nominees", "result", "category"):
                        category = cat_text
                        
                if category and first_ul:
                    li_items = cell.find_all("li")
                    for li in li_items:
                        nominee, film = extract_film_and_nominee(li)
                        is_winner = is_winner_li(li)
                        
                        records.append({
                            "category": category,
                            "nominee": nominee,
                            "film": film,
                            "winner": 1 if is_winner else 0
                        })
                        
    return records

def run_test():
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    recs = parse_ceremony_page(response.text, "2013 AMVCA", 2013, url)
    print(f"Total parsed: {len(recs)}")
    print("First 10 records:")
    for r in recs[:10]:
        print(" ", r)

run_test()
