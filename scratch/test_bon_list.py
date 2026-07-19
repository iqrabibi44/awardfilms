import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2014_Best_of_Nollywood_Awards"
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

def parse_list_page(html):
    soup = BeautifulSoup(html, "lxml")
    records = []
    
    exclude_headings = {"contents", "ceremony", "presenters", "performers", "references", "external links", "winners and nominees", "history", "venue", "categories", "notes", "lead role", "supporting role"}
    
    headings = soup.find_all(["h2", "h3", "h4"])
    for heading in headings:
        category = clean_text(heading.get_text())
        if not category or category.lower() in exclude_headings or len(category) > 100:
            continue
            
        # Determine starting element for sibling search (heading or its wrapper div)
        start_elem = heading
        if heading.parent and heading.parent.name == "div" and any(cls.startswith("mw-heading") for cls in heading.parent.get("class", [])):
            start_elem = heading.parent
            
        sibling = start_elem.next_sibling
        while sibling:
            if sibling.name in ("h2", "h3", "h4") or (sibling.name == "div" and any(cls.startswith("mw-heading") for cls in sibling.get("class", []))):
                break
                
            if sibling.name == "ul":
                li_items = sibling.find_all("li")
                for li in li_items:
                    nominee, film = extract_film_and_nominee(li)
                    is_winner = is_winner_li(li)
                    
                    records.append({
                        "category": category,
                        "nominee": nominee,
                        "film": film,
                        "winner": 1 if is_winner else 0
                    })
            sibling = sibling.next_sibling
            
    return records

def run_test():
    response = requests.get(url, headers=headers)
    recs = parse_list_page(response.text)
    print(f"Total parsed: {len(recs)}")
    print("First 10 records:")
    for r in recs[:10]:
        print(" ", r)

run_test()
