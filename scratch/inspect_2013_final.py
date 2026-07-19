import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2013_Africa_Magic_Viewers%27_Choice_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

tables = soup.find_all("table", class_=re.compile("wikitable"))
if tables:
    print(f"Table rows count: {len(tables[0].find_all('tr'))}")
    row = tables[0].find_all("tr")[0]
    cells = row.find_all(["td", "th"])
    for idx, c in enumerate(cells):
        print(f"Cell {idx} (tag={c.name}):")
        print(str(c)[:1500])
        print("="*40)
