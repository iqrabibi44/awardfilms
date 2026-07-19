import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/Africa_International_Film_Festival"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

tables = soup.find_all("table", class_=re.compile("wikitable"))
print(f"Found {len(tables)} wikitables")
for idx, table in enumerate(tables):
    prev_h = table.find_previous(["h2", "h3", "h4"])
    year = None
    heading_found = "None"
    while prev_h:
        prev_text = prev_h.get_text()
        year_match = re.search(r'\b(20\d{2})\b', prev_text)
        if year_match:
            year = int(year_match.group(1))
            heading_found = prev_text
            break
        prev_h = prev_h.find_previous(["h2", "h3", "h4"])
        
    print(f"Table {idx}: Found Heading='{heading_found.strip()}' -> Year={year}")
