import requests
from bs4 import BeautifulSoup
import re

headers = {"User-Agent": "AwardFilmsScraper/1.0"}
proxies = {
    "http": "socks5h://user_0:pass_0@127.0.0.1:9050",
    "https": "socks5h://user_0:pass_0@127.0.0.1:9050",
}

url = "https://en.wikipedia.org/wiki/El_Gouna_Film_Festival"
print(f"Fetching: {url}")
resp = requests.get(url, headers=headers, proxies=proxies, timeout=30)
print(f"Status: {resp.status_code}")

soup = BeautifulSoup(resp.text, "lxml")

print("\n--- All Headings ---")
for h in soup.find_all(["h2","h3","h4"]):
    print(f"  {h.name}: '{h.get_text(strip=True)}'")

print("\n--- Tables ---")
tables = soup.find_all("table", class_=re.compile("wikitable"))
print(f"Total wikitables: {len(tables)}")
for i, t in enumerate(tables[:5]):
    rows = t.find_all("tr")
    print(f"\nTable {i}: {len(rows)} rows. Prev heading: '{t.find_previous(['h2','h3','h4']).get_text(strip=True) if t.find_previous(['h2','h3','h4']) else 'none'}'")
    for r in rows[:6]:
        cells = r.find_all(["th","td"])
        print(f"  Row: {[c.get_text(strip=True)[:60] for c in cells[:5]]}")

print("\n--- Lists under year headings ---")
headings = soup.find_all(["h2","h3","h4"])
for heading in headings:
    htxt = heading.get_text(strip=True)
    # Only show ones with year or award-related content
    if not re.search(r'\b(20\d{2}|winner|award|prize)\b', htxt, re.I):
        continue
    
    start = heading
    if heading.parent and heading.parent.name == "div":
        start = heading.parent
    
    sibling = start.next_sibling
    count = 0
    while sibling and count < 8:
        if hasattr(sibling, 'name') and sibling.name in ("h2","h3","h4"):
            break
        if hasattr(sibling, 'name') and sibling.name == "div" and any(
            cls.startswith("mw-heading") for cls in sibling.get("class", [])
        ):
            break
        if hasattr(sibling, 'name') and sibling.name:
            print(f"\n  Heading '{htxt}' -> <{sibling.name}>: '{sibling.get_text(strip=True)[:150]}'")
            if sibling.name in ("ul","ol"):
                for item in sibling.find_all("li")[:5]:
                    print(f"    li: '{item.get_text(strip=True)[:120]}'")
            count += 1
        sibling = sibling.next_sibling
