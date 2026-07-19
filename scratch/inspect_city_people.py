import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/City_People_Entertainment_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

print("--- Headings ---")
for h in soup.find_all(["h2", "h3", "h4"]):
    print(f"Heading: '{h.get_text(strip=True)}'")

print("\n--- Tables ---")
tables = soup.find_all("table")
print(f"Total tables: {len(tables)}")
for idx, t in enumerate(tables):
    classes = t.get("class", [])
    print(f"Table {idx} classes: {classes}")
    rows = t.find_all("tr")
    print(f"  Rows count: {len(rows)}")
    for r_idx, r in enumerate(rows[:5]):
        cells = r.find_all(["td", "th"])
        print(f"    Row {r_idx} text:", [c.get_text(strip=True) for c in cells[:4]])
