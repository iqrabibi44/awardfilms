import requests
from bs4 import BeautifulSoup
import re

headers = {"User-Agent": "AwardFilmsScraper/1.0"}
proxies = {
    "http": "socks5h://user_0:pass_0@127.0.0.1:9050",
    "https": "socks5h://user_0:pass_0@127.0.0.1:9050",
}

url = "https://en.wikipedia.org/wiki/List_of_FESPACO_award_winners"
resp = requests.get(url, headers=headers, proxies=proxies, timeout=30)
soup = BeautifulSoup(resp.text, "lxml")

# Show full content under 2023 heading  
headings = soup.find_all(["h2","h3","h4"])
for heading in headings:
    htxt = heading.get_text(strip=True)
    if "2023" not in htxt and "2021" not in htxt:
        continue
    
    print(f"\n{'='*60}")
    print(f"HEADING: {htxt}")
    print('='*60)
    
    start = heading
    if heading.parent and heading.parent.name == "div" and any(
        cls.startswith("mw-heading") for cls in heading.parent.get("class",[])
    ):
        start = heading.parent
    
    sib = start.next_sibling
    count = 0
    while sib and count < 40:
        if hasattr(sib, 'name') and sib.name in ("h2","h3","h4"):
            break
        if hasattr(sib, 'name') and sib.name == "div" and any(
            cls.startswith("mw-heading") for cls in sib.get("class",[])
        ):
            break
        if hasattr(sib, 'name') and sib.name:
            txt = sib.get_text(strip=True)
            if txt:
                print(f"<{sib.name}>: {txt[:300]}")
                if sib.name in ("ul","ol"):
                    for li in sib.find_all(["li","dt","dd"])[:15]:
                        print(f"  ITEM: {li.get_text(strip=True)[:150]}")
        count += 1
        sib = sib.next_sibling
