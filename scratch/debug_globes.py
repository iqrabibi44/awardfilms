import requests
from bs4 import BeautifulSoup
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}
url = "https://en.wikipedia.org/wiki/81st_Golden_Globe_Awards"
resp = requests.get(url, headers=HEADERS)
soup = BeautifulSoup(resp.content, 'lxml')

tables = soup.find_all('table', class_='wikitable')
for table in tables:
    cells = table.find_all(['td', 'th'])
    for cell in cells:
        cat_elem = cell.find('b') or cell.find('div') or cell.find('th')
        if not cat_elem: continue
        category = cat_elem.get_text()
        print(f"Cat Elem Text: {category}")
        ul = cell.find('ul')
        if not ul:
            print("No ul found")
        else:
            print("Found ul")
            
        break
    break
