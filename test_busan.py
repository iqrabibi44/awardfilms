import requests
from bs4 import BeautifulSoup

url = "https://en.wikipedia.org/wiki/Busan_International_Film_Festival"
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'lxml')

headings = soup.find_all(['h2', 'h3'])
print("Headings:")
for h in headings:
    print(h.get_text(strip=True))

tables = soup.find_all('table', class_='wikitable')
for i, table in enumerate(tables[:5]):
    prev = table.find_previous_sibling(['h2', 'h3'])
    prev_text = prev.get_text(strip=True) if prev else "None"
    print(f"Table {i} - Section: {prev_text}")
