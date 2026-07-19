import requests
from bs4 import BeautifulSoup

def inspect_html(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.content, 'lxml')
    tables = soup.find_all('table', class_='wikitable')
    if tables:
        for t in tables[:1]:
            tds = t.find_all('td')
            if tds:
                print(f"--- HTML for {url} first TD ---")
                print(tds[0].prettify())

inspect_html("https://en.wikipedia.org/wiki/81st_Golden_Globe_Awards")
inspect_html("https://en.wikipedia.org/wiki/1st_Golden_Globe_Awards")
