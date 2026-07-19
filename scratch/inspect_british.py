import requests
from bs4 import BeautifulSoup
import re

HEADERS = {"User-Agent": "AwardFilmsScraper/1.0"}
TOR_SOCKS_PORT = 9050
proxies = {
    "http": f"socks5h://user_0:pass_0@127.0.0.1:{TOR_SOCKS_PORT}",
    "https": f"socks5h://user_0:pass_0@127.0.0.1:{TOR_SOCKS_PORT}",
}

urls = {
    "BAFTA": "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Film",
    "BAFTA_Main": "https://en.wikipedia.org/wiki/British_Academy_Film_Awards",
    "BIFA": "https://en.wikipedia.org/wiki/British_Independent_Film_Awards",
    "BIFA_Best_British_Independent_Film": "https://en.wikipedia.org/wiki/BIFA_Award_for_Best_British_Independent_Film",
    "London_Critics": "https://en.wikipedia.org/wiki/London_Film_Critics%27_Circle",
    "London_Critics_Film_of_the_Year": "https://en.wikipedia.org/wiki/London_Film_Critics%27_Circle_Award_for_Film_of_the_Year",
    "Evening_Standard": "https://en.wikipedia.org/wiki/Evening_Standard_British_Film_Awards"
}

for name, url in urls.items():
    try:
        resp = requests.get(url, headers=HEADERS, proxies=proxies, timeout=20)
        has_table = "wikitable" in resp.text if resp.status_code == 200 else False
        has_content = resp.status_code == 200 and len(resp.text) > 5000
        
        tables_count = 0
        if has_content:
            soup = BeautifulSoup(resp.text, "lxml")
            tables = soup.find_all("table", class_=re.compile("wikitable"))
            tables_count = len(tables)
        
        print(f"[{name}] {resp.status_code} | tables={tables_count} | {url}")
        
    except Exception as e:
        print(f"[{name}] Failed: {e}")
