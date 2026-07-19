import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/City_People_Entertainment_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

print("--- Inspecting non-table content under headings ---")
exclude_headings = {"contents", "references", "external links"}

headings = soup.find_all(["h2", "h3", "h4"])
for heading in headings:
    heading_text = heading.get_text(strip=True)
    if heading_text.lower() in exclude_headings:
        continue
        
    print(f"\nHeading: '{heading_text}'")
    
    start_elem = heading
    if heading.parent and heading.parent.name == "div" and any(cls.startswith("mw-heading") for cls in heading.parent.get("class", [])):
        start_elem = heading.parent
        
    sibling = start_elem.next_sibling
    count = 0
    while sibling and count < 3:
        if sibling.name in ("h2", "h3", "h4") or (sibling.name == "div" and any(cls.startswith("mw-heading") for cls in sibling.get("class", []))):
            break
            
        if sibling.name == "ul":
            lis = sibling.find_all("li")
            print(f"  ul with {len(lis)} items. Sample: {[li.get_text(strip=True)[:100] for li in lis[:3]]}")
            count += 1
        elif sibling.name == "p":
            print(f"  p text: '{sibling.get_text(strip=True)[:150]}'")
            count += 1
        sibling = sibling.next_sibling
