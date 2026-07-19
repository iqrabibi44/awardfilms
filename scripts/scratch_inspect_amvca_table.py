import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2023_Africa_Magic_Viewers%27_Choice_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

tables = soup.find_all("table", class_=re.compile("wikitable"))
if tables:
    table = tables[0]
    rows = table.find_all("tr")
    print(f"Total rows in Table 1: {len(rows)}")
    for idx, row in enumerate(rows[:5]):
        print(f"\n--- Row {idx} ---")
        cells = row.find_all(["td", "th"])
        print(f"Number of cells: {len(cells)}")
        for c_idx, cell in enumerate(cells):
            print(f"  Cell {c_idx} (name={cell.name}):")
            print(f"    Raw: {str(cell)[:300]}...")
            print(f"    Text: {cell.get_text(strip=True)}")
