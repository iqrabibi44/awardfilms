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

# Find the 1st year h2 and show all its siblings
headings = soup.find_all("h2")
for heading in headings[:5]:
    heading_text = heading.get_text(strip=True)
    if "1969" not in heading_text and "1970" not in heading_text:
        continue
    
    print(f"\n=== Heading: {heading_text} ===")
    
    start_elem = heading
    if heading.parent and heading.parent.name == "div" and any(
        cls.startswith("mw-heading") for cls in heading.parent.get("class", [])
    ):
        start_elem = heading.parent
        print("  (wrapped in mw-heading div)")
    
    sibling = start_elem.next_sibling
    count = 0
    while sibling and count < 20:
        if hasattr(sibling, 'name') and sibling.name in ("h2", "h3"):
            break
        if hasattr(sibling, 'name') and sibling.name == "div" and any(
            cls.startswith("mw-heading") for cls in sibling.get("class", [])
        ):
            break
        if hasattr(sibling, 'name') and sibling.name:
            print(f"  Sibling tag: <{sibling.name}> class={sibling.get('class',[])} text='{sibling.get_text(strip=True)[:120]}'")
            if sibling.name in ("ul", "dl", "ol"):
                for li in sibling.find_all(["li", "dt", "dd"])[:8]:
                    print(f"    Item: '{li.get_text(strip=True)[:120]}'")
                    print(f"    HTML: {str(li)[:200]}")
        count += 1
        sibling = sibling.next_sibling
