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

headings = soup.find_all(["h2","h3"])
for heading in headings:
    heading_text = heading.get_text(strip=True)
    # Show 1976 which was first competitive edition
    if "1979" not in heading_text and "1981" not in heading_text:
        continue
    
    print(f"\n=== {heading_text} ===")
    
    start_elem = heading
    if heading.parent and heading.parent.name == "div" and any(
        cls.startswith("mw-heading") for cls in heading.parent.get("class", [])
    ):
        start_elem = heading.parent
    
    sibling = start_elem.next_sibling
    count = 0
    while sibling and count < 30:
        if hasattr(sibling, 'name') and sibling.name in ("h2", "h3"):
            break
        if hasattr(sibling, 'name') and sibling.name == "div" and any(
            cls.startswith("mw-heading") for cls in sibling.get("class", [])
        ):
            break
        if hasattr(sibling, 'name') and sibling.name:
            tag = sibling.name
            text_preview = sibling.get_text(strip=True)[:150]
            print(f"  <{tag}>: {text_preview}")
            if tag in ("ul", "dl", "ol"):
                for item in sibling.find_all(["li", "dt", "dd"])[:10]:
                    print(f"    - {item.get_text(strip=True)[:120]}")
        count += 1
        sibling = sibling.next_sibling
    print("---")
