import requests
from bs4 import BeautifulSoup
import re

HEADERS = {"User-Agent": "AwardFilmsScraper/1.0"}
TOR_SOCKS_PORT = 9050
proxies = {
    "http": f"socks5h://user_0:pass_0@127.0.0.1:{TOR_SOCKS_PORT}",
    "https": f"socks5h://user_0:pass_0@127.0.0.1:{TOR_SOCKS_PORT}",
}

url = "https://en.wikipedia.org/wiki/Evening_Standard_British_Film_Awards"
resp = requests.get(url, headers=HEADERS, proxies=proxies, timeout=20)
soup = BeautifulSoup(resp.text, "lxml")

print("=== HEADINGS ===")
for h in soup.find_all(["h2","h3","h4"]):
    print(f"  {h.name}: '{h.get_text(strip=True)}'")

print("\n=== LISTS under headings ===")
headings = soup.find_all(["h2","h3","h4"])
for heading in headings:
    htxt = heading.get_text(strip=True)
    if "contents" in htxt.lower() or "reference" in htxt.lower():
        continue
    
    start = heading
    if heading.parent and heading.parent.name == "div" and any(
        cls.startswith("mw-heading") for cls in heading.parent.get("class",[])
    ):
        start = heading.parent
    
    sib = start.next_sibling
    count = 0
    while sib and count < 8:
        if hasattr(sib, 'name') and sib.name in ("h2","h3","h4"):
            break
        if hasattr(sib, 'name') and sib.name:
            if sib.name in ("ul","ol"):
                print(f"Heading: '{htxt}' -> <{sib.name}>")
                for li in sib.find_all("li")[:3]:
                    print(f"  {li.get_text(strip=True)[:100]}")
        count += 1
        sib = sib.next_sibling
