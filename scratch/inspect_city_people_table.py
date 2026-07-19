import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/City_People_Entertainment_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

tables = soup.find_all("table", class_=re.compile("wikitable"))
if tables:
    table = tables[0]
    rows = table.find_all("tr")
    print(f"Table 3 rows count: {len(rows)}")
    for r_idx, row in enumerate(rows):
        cells = row.find_all(["td", "th"])
        print(f"Row {r_idx}: {[c.get_text(strip=True) for c in cells]}")
