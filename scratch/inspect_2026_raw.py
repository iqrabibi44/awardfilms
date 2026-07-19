import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2026_Africa_Magic_Viewers%27_Choice_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

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
                print(f"Table {t_idx}, Row {r_idx}, Cell {c_idx}:")
                print(str(cell)[:1000])
                print("-" * 50)
