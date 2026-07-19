import requests
from bs4 import BeautifulSoup
import re

def extract_lists_from_ul(ul):
    results = []
    first_li = ul.find('li', recursive=False)
    if not first_li:
        return results
        
    nested_ul = first_li.find(['ul', 'dl'], recursive=False)
    if nested_ul:
        clone = BeautifulSoup(str(first_li), 'lxml').find('li')
        if clone.find(['ul', 'dl']):
            clone.find(['ul', 'dl']).decompose()
        winner_text = clone.get_text()
        results.append((winner_text, True))
        
        for n_li in nested_ul.find_all('li', recursive=False):
            results.append((n_li.get_text(), False))
    else:
        lis = ul.find_all('li', recursive=False)
        for i, li in enumerate(lis):
            is_winner = (i == 0) or bool(li.find('b'))
            results.append((li.get_text(), is_winner))
            
    return results

url = "https://en.wikipedia.org/wiki/81st_Golden_Globe_Awards"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(resp.content, 'lxml')
tables = soup.find_all('table', class_='wikitable')
cell = tables[0].find('td')
ul = cell.find('ul')
print("UL found:", bool(ul))
print("First LI:", ul.find('li', recursive=False) is not None)
res = extract_lists_from_ul(ul)
print(f"Items found: {len(res)}")
