import requests
from bs4 import BeautifulSoup
import re

HEADERS = {"User-Agent": "AwardFilmsScraper/1.0"}
proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}

url = "https://en.wikipedia.org/wiki/German_Film_Award"
resp = requests.get(url, headers=HEADERS, proxies=proxies, timeout=20)
soup = BeautifulSoup(resp.text, "lxml")

for a in soup.find_all("a", href=True):
    if "German_Film_Award_for" in a["href"]:
        print(a.get_text(), "->", a["href"])
    elif "Deutscher_Filmpreis" in a["href"]:
        print(a.get_text(), "->", a["href"])
