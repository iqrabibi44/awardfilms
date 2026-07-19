import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2017_Best_of_Nollywood_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

tables = soup.find_all("table", class_=re.compile("wikitable"))
if tables:
    cell = tables[0].find_all("tr")[1].find_all("td")[0]
    print("--- Cell HTML ---")
    print(str(cell))
    print("\n--- Children tags ---")
    for child in cell.children:
        if child.name:
            print(f"Child tag: {child.name}, text: '{child.get_text(strip=True)}'")
        else:
            print(f"Text child: '{child.strip()}'")
