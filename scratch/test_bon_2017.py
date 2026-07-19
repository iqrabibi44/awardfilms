import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2017_Best_of_Nollywood_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\[[^\]]+\]', '', text)
    text = text.replace('†', '').replace('*', '').replace('‡', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_film_and_nominee_element(elem):
    el_copy = BeautifulSoup(str(elem), "lxml")
    for tag in el_copy.find_all(["ul", "ol", "p"]):
        tag.decompose()
    for tag in el_copy.find_all(["sup", "span"]):
        tag.decompose()
        
    i_tags = el_copy.find_all("i")
    if i_tags:
        film_candidate = clean_text(i_tags[0].get_text())
        for i_t in el_copy.find_all("i"):
            i_t.decompose()
        rest_candidate = clean_text(el_copy.get_text())
        
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
        text = clean_text(el_copy.get_text())
        text = re.sub(r'^[\*\s\•\\–\—\-\[\]\(\)]+', '', text)
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

def get_nominees_from_cell(cell):
    li_items = cell.find_all("li")
    if li_items:
        res = []
        for li in li_items:
            nom, flm = extract_film_and_nominee_element(li)
            is_win = is_winner_li(li)
            if nom or flm:
                res.append((nom, flm, is_win))
        return res
        
    p_items = cell.find_all("p")
    b_items = cell.find_all(["b", "strong"], recursive=False)
    
    res = []
    for b in b_items:
        if b.find(["ul", "ol", "p"]):
            continue
        nom, flm = extract_film_and_nominee_element(b)
        if nom or flm:
            res.append((nom, flm, True))
            
    for p in p_items:
        nom, flm = extract_film_and_nominee_element(p)
        if nom or flm:
            is_win = is_winner_li(p)
            res.append((nom, flm, is_win))
            
    if not res:
        cell_html = str(cell)
        lines = re.split(r'<br\s*/?>', cell_html, flags=re.IGNORECASE)
        if len(lines) <= 1:
            cell_text = cell.get_text()
            lines = [ln.strip() for ln in cell_text.split("\n") if ln.strip()]
            
        for line in lines:
            line_soup = BeautifulSoup(line, "lxml")
            text = clean_text(line_soup.get_text())
            if text and len(text) > 3 and text.lower() not in ("winner", "nominees", "result", "category"):
                nom, flm = extract_film_and_nominee_element(line_soup)
                is_win = is_winner_li(line_soup)
                if nom or flm:
                    res.append((nom, flm, is_win))
                    
    return res

def parse_tables(soup, ceremony_name, year, source_url):
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
                
            if all(cell.name == "th" for cell in cells):
                current_categories = [clean_text(cell.get_text()) for cell in cells]
                continue
                
            for col_idx, cell in enumerate(cells):
                category = None
                nominees_list = get_nominees_from_cell(cell)
                if not nominees_list:
                    continue
                    
                first_nom, first_film, _ = nominees_list[0]
                cell_text = cell.get_text()
                
                # Check for category at the top of cell
                prefix_clean = None
                if first_nom and first_nom in cell_text:
                    prefix = cell_text.split(first_nom)[0]
                    prefix_clean = clean_text(prefix)
                elif first_film and first_film in cell_text:
                    prefix = cell_text.split(first_film)[0]
                    prefix_clean = clean_text(prefix)
                    
                # Real categories must be longer than 5 chars and contain text
                if prefix_clean and len(prefix_clean) > 5 and re.search(r'[A-Za-z]', prefix_clean) and prefix_clean.lower() not in ("winner", "nominees", "result", "category"):
                    category = prefix_clean
                    
                # Fallback Layout 2
                if not category and len(cells) == 2:
                    nominees_0 = get_nominees_from_cell(cells[0])
                    nominees_1 = get_nominees_from_cell(cells[1])
                    if nominees_1 and not nominees_0:
                        cat_text = clean_text(cells[0].get_text())
                        if cat_text and len(cat_text) < 120 and cat_text.lower() not in ("winner", "nominees", "result", "category"):
                            if col_idx == 1:
                                category = cat_text
                                nominees_list = nominees_1
                                
                # Fallback Layout 1
                if not category and current_categories and col_idx < len(current_categories):
                    cat_text = current_categories[col_idx]
                    if cat_text and cat_text.lower() not in ("winner", "nominees", "result", "category"):
                        category = cat_text
                        
                if category and nominees_list:
                    for nom, flm, is_win in nominees_list:
                        records.append({
                            "category": category,
                            "nominee": nom,
                            "film": flm,
                            "winner": 1 if is_win else 0
                        })
    return records

def run_test():
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    recs = parse_tables(soup, "2017 BON", 2017, url)
    print(f"Total parsed: {len(recs)}")
    print("First 15 records:")
    for r in recs[:15]:
        print(" ", r)

run_test()
