import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://en.wikipedia.org/wiki/Bavarian_Film_Awards_(Best_Producing)"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, proxies={"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"})
soup = BeautifulSoup(resp.text, "lxml")

tables = soup.find_all("table")
for i, t in enumerate(tables):
    try:
        df = pd.read_html(str(t))[0]
        print(f"Table {i} shape: {df.shape}")
        print(df.columns.tolist())
    except:
        print(f"Table {i} failed to parse with pandas")
