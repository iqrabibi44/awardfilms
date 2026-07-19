import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2013_Africa_Magic_Viewers%27_Choice_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

print("--- Wikitables ---")
tables = soup.find_all("table", class_=re.compile("wikitable"))
print(f"Total wikitables: {len(tables)}")
for i, t in enumerate(tables):
    rows = t.find_all("tr")
    print(f"Table {i} rows: {len(rows)}")
    for idx, r in enumerate(rows[:5]):
        th_cells = r.find_all("th")
        td_cells = r.find_all("td")
        print(f"  Row {idx}: th={len(th_cells)}, td={len(td_cells)}")
        if th_cells:
            print("    th text:", [th.get_text(strip=True) for th in th_cells])
        if td_cells:
            print("    td text (first 100 chars):", str(td_cells[0].get_text(strip=True))[:100])
