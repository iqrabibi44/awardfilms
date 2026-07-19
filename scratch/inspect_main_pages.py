import requests
from bs4 import BeautifulSoup
import re

headers = {"User-Agent": "AwardFilmsScraper/1.0"}

def inspect_page(title):
    url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "lxml")
    
    print(f"\n================ INSPECTING: {title} ================")
    print("Headings:")
    for h in soup.find_all(["h2", "h3"])[:10]:
        print(f"  {h.name}: {h.get_text(strip=True)}")
        
    tables = soup.find_all("table", class_=re.compile("wikitable"))
    print(f"Total wikitables: {len(tables)}")
    for i, t in enumerate(tables[:3]):
        rows = t.find_all("tr")
        print(f"  Table {i} rows: {len(rows)}")
        if len(rows) > 0:
            headers_text = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])[:4]]
            print(f"    Headers: {headers_text}")
            if len(rows) > 1:
                cells = [c.get_text(strip=True) for c in rows[1].find_all(["th", "td"])[:4]]
                print(f"    Row 1: {cells}")

inspect_page("City People Entertainment Awards")
inspect_page("Africa International Film Festival")
