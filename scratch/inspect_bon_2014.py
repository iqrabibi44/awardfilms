import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2014_Best_of_Nollywood_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

print("--- Wikitables ---")
tables = soup.find_all("table", class_=re.compile("wikitable"))
print(f"Total wikitables: {len(tables)}")
for i, t in enumerate(tables):
    rows = t.find_all("tr")
    print(f"Table {i} rows: {len(rows)}")
    for idx, r in enumerate(rows[:3]):
        print(f"  Row {idx}: th={len(r.find_all('th'))}, td={len(r.find_all('td'))}")

print("\n--- Sections and lists ---")
for h in soup.find_all(["h2", "h3"])[:10]:
    heading_text = h.get_text(strip=True)
    print(f"Section: {heading_text}")
    sibling = h.next_sibling
    count = 0
    while sibling and sibling.name not in ("h2", "h3") and count < 3:
        if sibling.name == "ul":
            lis = sibling.find_all("li")
            print(f"  ul with {len(lis)} items. Sample: {[li.get_text(strip=True)[:100] for li in lis[:2]]}")
            count += 1
        sibling = sibling.next_sibling
