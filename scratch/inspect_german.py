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
    "German_Film_Award_Best_Fiction": "https://en.wikipedia.org/wiki/German_Film_Award_for_Best_Fiction_Film",
    "German_Film_Award_Best_Director": "https://en.wikipedia.org/wiki/German_Film_Award_for_Best_Director",
    "Bavarian_Film_Awards": "https://en.wikipedia.org/wiki/Bavarian_Film_Awards",
    "Berlin_Golden_Bear": "https://en.wikipedia.org/wiki/Golden_Bear",
    "Berlin_Silver_Bear_Director": "https://en.wikipedia.org/wiki/Silver_Bear_for_Best_Director"
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
