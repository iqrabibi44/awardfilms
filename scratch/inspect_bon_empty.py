import requests
from bs4 import BeautifulSoup
import re

urls = [
    ("2017 BON", "https://en.wikipedia.org/wiki/2017_Best_of_Nollywood_Awards"),
    ("2018 BON", "https://en.wikipedia.org/wiki/2018_Best_of_Nollywood_Awards"),
    ("2022 BON", "https://en.wikipedia.org/wiki/2022_Best_of_Nollywood_Awards")
]
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

for label, url in urls:
    print(f"\n=================== {label} ===================")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch {label} (HTTP {response.status_code})")
        continue
        
    soup = BeautifulSoup(response.text, "lxml")
    
    # Check tables
    tables = soup.find_all("table", class_=re.compile("wikitable"))
    print(f"Wikitables: {len(tables)}")
    
    # Check headings
    headings = soup.find_all(["h2", "h3", "h4"])
    print(f"Headings count: {len(headings)}")
    for h in headings[:10]:
        print("  Heading:", h.get_text(strip=True))
        
    # Check lists
    lists = soup.find_all("ul")
    print(f"Lists count: {len(lists)}")
