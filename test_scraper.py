import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://en.wikipedia.org/wiki/Grand_Bell_Award_for_Best_Actor"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

r = requests.get(url, headers=headers)
print("Status:", r.status_code)

soup = BeautifulSoup(r.text, "lxml")
tables = soup.find_all("table", class_=lambda c: c and "wikitable" in c)
print(f"Found {len(tables)} wikitables.")

for i, table in enumerate(tables):
    print(f"--- Table {i} ---")
    headers = []
    header_row = table.find("tr")
    if header_row:
        headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
    print("Headers:", headers)
    
    tr_list = table.find_all("tr")
    print("Row count:", len(tr_list))
    if len(tr_list) > 1:
        cells = tr_list[1].find_all(["td", "th"])
        print("First row data:", [c.get_text(strip=True) for c in cells])
