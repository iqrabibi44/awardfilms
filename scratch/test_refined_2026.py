import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2026_Africa_Magic_Viewers%27_Choice_Awards"
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

def run_test():
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    
    tables = soup.find_all("table", class_=re.compile("wikitable"))
    for t_idx, table in enumerate(tables):
        rows = table.find_all("tr")
        for r_idx, r in enumerate(rows):
            cells = r.find_all(["td", "th"])
            for c_idx, cell in enumerate(cells):
                text = cell.get_text()
                if "Best Scripted M-Net Original" in text or "The Low Priest" in text:
                    li_items = cell.find_all("li")
                    print(f"Found {len(li_items)} list items inside cell:")
                    for li in li_items:
                        nom, flm = extract_film_and_nominee(li)
                        print(f"  nominee: {nom} | film: {flm}")
                    break
run_test()
