import requests
from bs4 import BeautifulSoup

url = "https://en.wikipedia.org/wiki/Bavarian_Film_Awards_(Best_Producing)"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, proxies={"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"})
soup = BeautifulSoup(resp.text, "lxml")
for ul in soup.find_all("ul"):
    for li in ul.find_all("li"):
        print(li.get_text()[:100])
