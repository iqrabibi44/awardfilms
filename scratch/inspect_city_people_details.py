import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/City_People_Entertainment_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

print("--- Wikitables ---")
tables = soup.find_all("table", class_=re.compile("wikitable"))
print(f"Total: {len(tables)}")
for i, t in enumerate(tables):
    rows = t.find_all("tr")
    print(f"Table {i} rows: {len(rows)}")
    for r in rows[:3]:
        print("  Row:", [cell.get_text(strip=True) for cell in r.find_all(["th", "td"])[:4]])
        
print("\n--- Lists (ul) under Headings ---")
# Let's print some ul elements and their context
for parent in soup.find_all(["h2", "h3"]):
    print(f"Section: {parent.get_text(strip=True)}")
    sibling = parent.next_sibling
    while sibling and sibling.name not in ("h2", "h3"):
        if sibling.name == "ul":
            lis = sibling.find_all("li")
            print(f"  Found ul with {len(lis)} items. Sample: {[li.get_text(strip=True) for li in lis[:3]]}")
        elif sibling.name == "table":
            print(f"  Found table of class {sibling.get('class')}")
        sibling = sibling.next_sibling
