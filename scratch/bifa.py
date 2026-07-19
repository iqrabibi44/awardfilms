import re
from bs4 import BeautifulSoup

with open(r'C:\Users\INFOTECH\.gemini\antigravity-ide\brain\37b96083-d877-4fb8-9810-b552d1d6b47d\.system_generated\steps\96\content.md', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
for a in soup.find_all('a', href=True):
    href = a['href']
    if '/wiki/British_Independent_Film_Award_for_' in href:
        print(a.text.strip() or href, "https://en.wikipedia.org" + href.split('#')[0])
