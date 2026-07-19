import requests
from bs4 import BeautifulSoup
import re

headers = {"User-Agent": "AwardFilmsScraper/1.0"}
proxies = {
    "http": "socks5h://user_0:pass_0@127.0.0.1:9050",
    "https": "socks5h://user_0:pass_0@127.0.0.1:9050",
}

# Check FESPACO individual award category pages
FESPACO_CATEGORY_URLS = [
    "https://en.wikipedia.org/wiki/FESPACO_Stallion_of_Yennenga",
    "https://en.wikipedia.org/wiki/%C3%89talon_d%27or_de_Yennenga",
    "https://en.wikipedia.org/wiki/FESPACO_Best_Actor_Prize",
    "https://en.wikipedia.org/wiki/FESPACO_Best_Actress_Prize",
    "https://en.wikipedia.org/wiki/FESPACO_Paul_Robeson_Prize",
    "https://en.wikipedia.org/wiki/Oumarou_Ganda_Prize",
    "https://en.wikipedia.org/wiki/FESPACO_Best_Short_Film_Prize",
    "https://en.wikipedia.org/wiki/FESPACO_Best_Documentary_Prize",
    "https://en.wikipedia.org/wiki/FESPACO_Best_Screenplay_Prize",
]

for url in FESPACO_CATEGORY_URLS:
    resp = requests.get(url, headers=headers, proxies=proxies, timeout=20)
    has_table = "wikitable" in resp.text if resp.status_code == 200 else False
    has_content = resp.status_code == 200 and len(resp.text) > 5000
    print(f"{resp.status_code} | has_table={has_table} | {url}")
    
    if has_content:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
        tables = soup.find_all("table", class_=re.compile("wikitable"))
        if tables:
            t = tables[0]
            rows = t.find_all("tr")[:5]
            for r in rows:
                cells = r.find_all(["th","td"])
                print(f"  {[c.get_text(strip=True)[:50] for c in cells[:4]]}")
    import time, random
    time.sleep(random.uniform(0.3, 0.8))
