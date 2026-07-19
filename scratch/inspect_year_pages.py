import requests
from bs4 import BeautifulSoup
import re

headers = {"User-Agent": "AwardFilmsScraper/1.0"}
proxies = {
    "http": "socks5h://user_0:pass_0@127.0.0.1:9050",
    "https": "socks5h://user_0:pass_0@127.0.0.1:9050",
}

# Check if individual FESPACO year pages exist
fespaco_year_urls = [
    "https://en.wikipedia.org/wiki/19th_FESPACO",
    "https://en.wikipedia.org/wiki/20th_FESPACO",
    "https://en.wikipedia.org/wiki/21st_FESPACO",
    "https://en.wikipedia.org/wiki/FESPACO_2005",
    "https://en.wikipedia.org/wiki/FESPACO_2007",
    "https://en.wikipedia.org/wiki/FESPACO_2009",
    "https://en.wikipedia.org/wiki/FESPACO_2023",
    "https://en.wikipedia.org/wiki/28th_FESPACO",
    # El Gouna 2022/2023 pages
    "https://en.wikipedia.org/wiki/El_Gouna_Film_Festival_(2022)",
    "https://en.wikipedia.org/wiki/5th_El_Gouna_Film_Festival",
    "https://en.wikipedia.org/wiki/El_Gouna_Film_Festival_2022",
    "https://en.wikipedia.org/wiki/6th_El_Gouna_Film_Festival",
    "https://en.wikipedia.org/wiki/El_Gouna_Film_Festival_2023",
]

import time, random
for url in fespaco_year_urls:
    resp = requests.get(url, headers=headers, proxies=proxies, timeout=20)
    tables = 0
    if resp.status_code == 200:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
        tables = len(soup.find_all("table", class_=re.compile("wikitable")))
        headings = [h.get_text(strip=True) for h in soup.find_all(["h2","h3"])[:5]]
    else:
        headings = []
    print(f"{resp.status_code} | tables={tables} | {url}")
    if resp.status_code == 200:
        print(f"   headings: {headings[:3]}")
    time.sleep(random.uniform(0.3, 0.7))
