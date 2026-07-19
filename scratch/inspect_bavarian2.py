import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "GermanCinemaScraper/1.0"}
url = "https://en.wikipedia.org/wiki/Bavarian_Film_Awards"
resp = requests.get(url, headers=HEADERS, proxies={"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}, timeout=20)
soup = BeautifulSoup(resp.text, "lxml")

h2 = soup.find(id="Categories")
if h2:
    start = h2.parent
    sibling = start.next_sibling
    while sibling:
        if getattr(sibling, "name", None) in ["h2", "h3"]:
            break
        if getattr(sibling, "name", None) == "ul":
            for a in sibling.find_all("a", href=True):
                print(a.get_text(), "https://en.wikipedia.org" + a["href"])
        sibling = sibling.next_sibling
