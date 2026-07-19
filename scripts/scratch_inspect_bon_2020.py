import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2020_Best_of_Nollywood_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

print("--- Tables ---")
tables = soup.find_all("table", class_=re.compile("wikitable"))
print(f"Total wikitables: {len(tables)}")
for i, t in enumerate(tables):
    rows = t.find_all("tr")
    print(f"Table {i}: rows={len(rows)}")
    if len(rows) > 0:
        cells = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])[:3]]
        print(f"  Row 0 cells: {cells}")
        if len(rows) > 1:
            cells1 = [c.get_text(strip=True) for c in rows[1].find_all(["th", "td"])[:3]]
            print(f"  Row 1 cells: {cells1}")
