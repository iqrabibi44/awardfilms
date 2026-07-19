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
    # Only decompose nested list tags, NOT p tags!
    for tag in el_copy.find_all(["ul", "ol", "li"]):
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
            nominee = re.sub(r'^[–\—\-\s\•\\–\—\xa0]+', '', nominee)
            nominee = re.sub(r'[–\—\-\s\•\\–\—\xa0]+$', '', nominee)
            nominee = clean_text(nominee)
    else:
        text = clean_text(el_copy.get_text())
        text = re.sub(r'^[\*\s\•\\–\—\-\[\]\(\)\xa0]+', '', text)
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
            res.append((nom, flm, is_win))
        return res
        
    p_items = cell.find_all("p")
    b_items = cell.find_all(["b", "strong"], recursive=False)
    
    print(f"Debug: found {len(b_items)} bold items, {len(p_items)} paragraph items")
    res = []
    for b in b_items:
        nom, flm = extract_film_and_nominee_element(b)
        print(f"  Bold item: nom='{nom}', flm='{flm}'")
        if nom or flm:
            res.append((nom, flm, True))
            
    for p in p_items:
        nom, flm = extract_film_and_nominee_element(p)
        print(f"  Paragraph item: nom='{nom}', flm='{flm}'")
        if nom or flm:
            is_win = is_winner_li(p)
            res.append((nom, flm, is_win))
            
    return res

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")
tables = soup.find_all("table", class_=re.compile("wikitable"))
if tables:
    cell = tables[0].find_all("tr")[1].find_all("td")[0]
    get_nominees_from_cell(cell)
