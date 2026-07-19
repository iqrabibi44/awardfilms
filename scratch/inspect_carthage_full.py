import requests
from bs4 import BeautifulSoup
import re

headers = {"User-Agent": "AwardFilmsScraper/1.0"}
proxies = {
    "http": "socks5h://user_0:pass_0@127.0.0.1:9050",
    "https": "socks5h://user_0:pass_0@127.0.0.1:9050",
}

# Inspect Carthage Film Festival Wikipedia page - find all individual year pages
url = "https://en.wikipedia.org/wiki/Carthage_Film_Festival"
resp = requests.get(url, headers=headers, proxies=proxies, timeout=30)
soup = BeautifulSoup(resp.text, "lxml")

print("=== HEADINGS ===")
for h in soup.find_all(["h2","h3","h4"]):
    print(f"  {h.name}: '{h.get_text(strip=True)}'")

print("\n=== TABLES ===")
tables = soup.find_all("table", class_=re.compile("wikitable"))
print(f"Total wikitables: {len(tables)}")
for i, t in enumerate(tables[:5]):
    rows = t.find_all("tr")
    prev = t.find_previous(["h2","h3","h4"])
    print(f"\nTable {i}: {len(rows)} rows")
    for r in rows[:6]:
        cells = r.find_all(["th","td"])
        print(f"  {[c.get_text(strip=True)[:70] for c in cells[:5]]}")

print("\n=== LINKS to year pages ===")
for link in soup.find_all("a", href=True):
    href = link["href"]
    if re.search(r'\d{4}.*[Cc]arthage', href) or re.search(r'[Cc]arthage.*\d{4}', href):
        print(f"  {link.get_text(strip=True)}: {href}")
