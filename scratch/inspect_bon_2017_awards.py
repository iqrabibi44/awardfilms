import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2017_Best_of_Nollywood_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

print("--- Inspecting content after 'Awards' heading ---")
awards_h = None
for h in soup.find_all(["h2", "h3", "h4"]):
    if "awards" in h.get_text().lower():
        awards_h = h
        break
        
if not awards_h:
    # Try parent div
    for h in soup.find_all("div", class_=re.compile("mw-heading")):
        if "awards" in h.get_text().lower():
            awards_h = h
            break

if awards_h:
    start = awards_h
    if awards_h.parent and awards_h.parent.name == "div" and any(cls.startswith("mw-heading") for cls in awards_h.parent.get("class", [])):
        start = awards_h.parent
        
    sibling = start.next_sibling
    count = 0
    while sibling and count < 10:
        if sibling.name:
            print(f"[{sibling.name}]:")
            print(str(sibling)[:800])
            print("-" * 50)
            count += 1
        sibling = sibling.next_sibling
