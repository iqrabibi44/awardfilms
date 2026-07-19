import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/2022_Best_of_Nollywood_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

print("--- Inspecting lists in 2022 BON ---")
lists = soup.find_all("ul")
print(f"Total lists: {len(lists)}")
for idx, ul in enumerate(lists):
    lis = ul.find_all("li")
    print(f"List {idx} has {len(lis)} items. Sample items:")
    for li in lis[:3]:
        print("  -", li.get_text(strip=True)[:150])
    print("-" * 50)
