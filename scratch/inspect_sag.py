import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://en.wikipedia.org/wiki/List_of_Screen_Actors_Guild_Awards_ceremonies"
TOR_SOCKS_PORT = 9050
proxies = {
    "http": f"socks5h://thread_sag:secret@127.0.0.1:{TOR_SOCKS_PORT}",
    "https": f"socks5h://thread_sag:secret@127.0.0.1:{TOR_SOCKS_PORT}",
}

try:
    resp = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, proxies=proxies, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'lxml')
    tables = soup.find_all('table', class_='wikitable')
    print(f"Found {len(tables)} wikitables on the main page.")
    if tables:
        for row in tables[0].find_all('tr')[1:5]:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 1:
                a = cells[0].find('a')
                if a:
                    print("Ceremony link:", urljoin("https://en.wikipedia.org", a.get('href', '')))
except Exception as e:
    print(f"Error fetching main page: {e}")
