import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "GermanCinemaScraper/1.0 (contact: student_scraper@example.com)"}
proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}

url = "https://en.wikipedia.org/wiki/German_Film_Award"
resp = requests.get(url, headers=HEADERS, proxies=proxies, timeout=20)
soup = BeautifulSoup(resp.text, "lxml")

for a in soup.find_all("a", href=True):
    text = a.get_text()
    if "best" in text.lower() or "bester" in text.lower():
        print(text, "->", a["href"])
