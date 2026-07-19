import requests
from bs4 import BeautifulSoup
import re

HEADERS = {"User-Agent": "GermanCinemaScraper/1.0"}
url = "https://en.wikipedia.org/wiki/Bavarian_Film_Awards"
resp = requests.get(url, headers=HEADERS, proxies={"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}, timeout=20)
soup = BeautifulSoup(resp.text, "lxml")

for h in soup.find_all(["h2", "h3", "h4"]):
    print(h.name, h.get_text().strip())
