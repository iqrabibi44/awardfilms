import requests
from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://fa.wikipedia.org/w/api.php"
params = {
    "action": "parse",
    "page": "تندیس زرین بهترین فیلم جشن سینمای ایران",
    "prop": "text",
    "utf8": "",
    "format": "json"
}
headers = {'User-Agent': 'Mozilla/5.0'}

r = requests.get(url, params=params, headers=headers)
data = r.json()
html = data['parse']['text']['*']
soup = BeautifulSoup(html, 'html.parser')

tables = soup.find_all("table", class_="wikitable")
print(f"Found {len(tables)} wikitables.")
for idx, t in enumerate(tables):
    rows = t.find_all("tr")
    headers = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
    print(f"Table {idx} (rows: {len(rows)}): {headers}")
    if len(rows) > 1:
        print(f"  First data row: {[c.get_text(strip=True) for c in rows[1].find_all(['th', 'td'])]}")
