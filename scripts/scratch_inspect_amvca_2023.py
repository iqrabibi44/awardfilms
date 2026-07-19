import requests
from bs4 import BeautifulSoup

url = "https://en.wikipedia.org/wiki/2023_Africa_Magic_Viewers%27_Choice_Awards"
headers = {"User-Agent": "AwardFilmsScraper/1.0"}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "lxml")

print("--- Headings ---")
for h in soup.find_all(["h2", "h3"])[:15]:
    print(f"  {h.name}: {h.get_text(strip=True)}")
    
print("\n--- Tables ---")
tables = soup.find_all("table")
print(f"Total tables: {len(tables)}")
for i, t in enumerate(tables[:5]):
    rows = t.find_all("tr")
    print(f"Table {i}: class={t.get('class')}, rows={len(rows)}")
    if len(rows) > 0:
        print("  Headers:", [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])[:5]])
