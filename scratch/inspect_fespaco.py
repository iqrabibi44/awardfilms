import requests
from bs4 import BeautifulSoup
import re

headers = {"User-Agent": "AwardFilmsScraper/1.0"}

proxies = {
    "http": "socks5h://user_0:pass_0@127.0.0.1:9050",
    "https": "socks5h://user_0:pass_0@127.0.0.1:9050",
}

url = "https://en.wikipedia.org/wiki/List_of_FESPACO_award_winners"
print(f"Fetching: {url}")
resp = requests.get(url, headers=headers, proxies=proxies, timeout=30)
print(f"Status: {resp.status_code}")

soup = BeautifulSoup(resp.text, "lxml")

print("\n--- Headings ---")
for h in soup.find_all(["h2","h3","h4"])[:30]:
    print(f"  {h.name}: '{h.get_text(strip=True)}'")

print("\n--- Tables ---")
tables = soup.find_all("table", class_=re.compile("wikitable"))
print(f"Total wikitables: {len(tables)}")
for i, t in enumerate(tables[:5]):
    rows = t.find_all("tr")
    print(f"\nTable {i}: {len(rows)} rows")
    for r in rows[:4]:
        cells = r.find_all(["th","td"])
        print(f"  Row: {[c.get_text(strip=True)[:60] for c in cells[:4]]}")

print("\n--- Lists ---")
uls = soup.find_all("ul")
print(f"Total uls: {len(uls)}")
for ul in uls[:5]:
    items = ul.find_all("li")
    print(f"  ul: {[li.get_text(strip=True)[:80] for li in items[:3]]}")
