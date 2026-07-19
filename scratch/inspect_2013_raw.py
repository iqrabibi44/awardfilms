import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2013_Africa_Magic_Viewers%27_Choice_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

tables = soup.find_all("table", class_=re.compile("wikitable"))
if tables:
    row = tables[0].find_all("tr")[0]
    cells = row.find_all(["td", "th"])
    print(f"Row has {len(cells)} cells")
    for idx, c in enumerate(cells):
        print(f"\n--- Cell {idx} ---")
        print("Raw HTML:")
        print(str(c)[:600])
