import requests
from bs4 import BeautifulSoup
import re

headers = {"User-Agent": "AwardFilmsScraper/1.0"}
proxies = {
    "http": "socks5h://user_0:pass_0@127.0.0.1:9050",
    "https": "socks5h://user_0:pass_0@127.0.0.1:9050",
}

url = "https://en.wikipedia.org/wiki/2019_El_Gouna_Film_Festival"
print(f"Fetching: {url}")
resp = requests.get(url, headers=headers, proxies=proxies, timeout=30)
print(f"Status: {resp.status_code}")

soup = BeautifulSoup(resp.text, "lxml")

print("\n--- Headings ---")
for h in soup.find_all(["h2","h3","h4"])[:20]:
    print(f"  {h.name}: '{h.get_text(strip=True)}'")

print("\n--- Tables ---")
tables = soup.find_all("table", class_=re.compile("wikitable"))
print(f"Total wikitables: {len(tables)}")
for i, t in enumerate(tables[:3]):
    rows = t.find_all("tr")
    print(f"\nTable {i}: {len(rows)} rows")
    for r in rows[:5]:
        cells = r.find_all(["th","td"])
        print(f"  Row: {[c.get_text(strip=True)[:60] for c in cells[:4]]}")

print("\n--- Lists under headings ---")
headings = soup.find_all(["h2","h3","h4"])
for heading in headings:
    htxt = heading.get_text(strip=True)
    if htxt.lower() in ("contents","references","external links","see also","cast","jury"):
        continue
    
    start = heading
    if heading.parent and heading.parent.name == "div":
        start = heading.parent
    
    sibling = start.next_sibling
    count = 0
    while sibling and count < 5:
        if hasattr(sibling, 'name') and sibling.name in ("h2","h3","h4"):
            break
        if hasattr(sibling, 'name') and sibling.name == "div" and any(
            cls.startswith("mw-heading") for cls in sibling.get("class", [])
        ):
            break
        if hasattr(sibling, 'name') and sibling.name in ("ul","ol","dl"):
            print(f"\nHeading '{htxt}' -> {sibling.name}:")
            for item in sibling.find_all(["li","dt","dd"])[:5]:
                print(f"    {item.get_text(strip=True)[:120]}")
            count += 1
        sibling = sibling.next_sibling
