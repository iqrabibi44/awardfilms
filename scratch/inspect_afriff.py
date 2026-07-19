import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/Africa_International_Film_Festival"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

print("--- All Tables ---")
tables = soup.find_all("table")
print(f"Total tables: {len(tables)}")
for i, t in enumerate(tables):
    classes = t.get("class", [])
    print(f"Table {i} classes: {classes}")
    rows = t.find_all("tr")
    print(f"  Rows: {len(rows)}")
    if rows:
        th = rows[0].find_all(["th", "td"])
        print(f"  Header text: {[cell.get_text(strip=True) for cell in th[:4]]}")

print("\n--- Headings (h2/h3) ---")
for h in soup.find_all(["h2", "h3"])[:15]:
    print(f"Heading: {h.get_text(strip=True)}")
