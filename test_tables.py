import requests
from bs4 import BeautifulSoup
import json

urls = [
    "https://en.wikipedia.org/wiki/Grand_Bell_Awards",
    "https://en.wikipedia.org/wiki/Busan_International_Film_Festival",
    "https://en.wikipedia.org/wiki/Chunsa_Film_Art_Awards",
    "https://en.wikipedia.org/wiki/Korean_Association_of_Film_Critics_Awards"
]

headers = {'User-Agent': 'Mozilla/5.0'}

for url in urls:
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'lxml')
    tables = soup.find_all('table', class_='wikitable')
    print(f"\n[{url}] - Found {len(tables)} wikitables")
    for i, table in enumerate(tables[:3]): # just first 3
        th_list = table.find('tr')
        if th_list:
            cols = [th.get_text(strip=True) for th in th_list.find_all(['th', 'td'])]
            print(f"  Table {i} cols: {cols}")
