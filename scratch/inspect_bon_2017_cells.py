import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2017_Best_of_Nollywood_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

tables = soup.find_all("table", class_=re.compile("wikitable"))
if tables:
    table = tables[0]
    rows = table.find_all("tr")
    print(f"Table has {len(rows)} rows")
    for r_idx, row in enumerate(rows[:3]):
        cells = row.find_all(["td", "th"])
        print(f"  Row {r_idx} cells count: {len(cells)}")
        for c_idx, cell in enumerate(cells):
            print(f"    Cell {c_idx} (tag={cell.name}):")
            print(str(cell)[:800])
            print("*" * 30)
