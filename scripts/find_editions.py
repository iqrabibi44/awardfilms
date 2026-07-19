import requests
from bs4 import BeautifulSoup
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://fa.wikipedia.org/w/api.php"
params = {
    "action": "parse",
    "page": "جشن سینمای ایران",
    "prop": "links",
    "utf8": "",
    "format": "json"
}
headers = {'User-Agent': 'Mozilla/5.0'}

r = requests.get(url, params=params, headers=headers)
data = r.json()
links = data['parse']['links']

print("Links on main page:")
for l in links:
    title = l['*']
    if "جشن سینمای ایران" in title:
        print("  -", title)
