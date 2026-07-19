import requests
from bs4 import BeautifulSoup
import re

headers = {"User-Agent": "AwardFilmsScraper/1.0"}
proxies = {
    "http": "socks5h://user_0:pass_0@127.0.0.1:9050",
    "https": "socks5h://user_0:pass_0@127.0.0.1:9050",
}

# Inspect ZIFF Wikipedia page - full content
url = "https://en.wikipedia.org/wiki/Zanzibar_International_Film_Festival"
resp = requests.get(url, headers=headers, proxies=proxies, timeout=30)
soup = BeautifulSoup(resp.text, "lxml")

print("=== HEADINGS ===")
for h in soup.find_all(["h2","h3","h4"]):
    print(f"  {h.name}: '{h.get_text(strip=True)}'")

print("\n=== TABLES ===")
tables = soup.find_all("table", class_=re.compile("wikitable"))
print(f"Total wikitables: {len(tables)}")
for i, t in enumerate(tables):
    rows = t.find_all("tr")
    prev = t.find_previous(["h2","h3","h4"])
    print(f"\nTable {i} (prev heading: '{prev.get_text(strip=True) if prev else 'none'}'): {len(rows)} rows")
    for r in rows[:8]:
        cells = r.find_all(["th","td"])
        texts = [c.get_text(strip=True)[:60] for c in cells[:5]]
        print(f"  {texts}")
