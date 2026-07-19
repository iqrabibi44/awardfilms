import requests
from bs4 import BeautifulSoup
import re
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://en.wikipedia.org/wiki/Buenos_Aires_International_Festival_of_Independent_Cinema"
headers_req = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

r = requests.get(url, headers=headers_req)
soup = BeautifulSoup(r.text, 'html.parser')

tables = soup.find_all("table", class_=lambda c: c and "wikitable" in c)
if len(tables) < 2:
    print("Not enough tables found")
    exit(1)
    
csv_rows = []

# Table 0: Best Film (International Competition)
t0 = tables[0]
rows0 = t0.find_all("tr")
for r_idx in range(1, len(rows0)):
    row = rows0[r_idx]
    cells = row.find_all(["th", "td"])
    texts = [c.get_text(" ", strip=True) for c in cells]
    
    if len(texts) < 4:
        continue
        
    year_str = re.sub(r"\[.*?\]", "", texts[0]).strip()
    m = re.search(r"^(\d{4})", year_str)
    if not m:
        continue
    year_val = int(m.group(1))
    
    film_val = re.sub(r"\[.*?\]", "", texts[1]).strip()
    nominee_val = re.sub(r"\[.*?\]", "", texts[3]).strip()
    
    if not film_val and not nominee_val:
        continue
        
    csv_rows.append({
        "year": year_val,
        "ceremony": "BAFICI Awards",
        "category": "Best Film",
        "nominee": nominee_val,
        "film": film_val,
        "won": 1
    })

# Table 1: Other Awards
t1 = tables[1]
rows1 = t1.find_all("tr")

for r_idx in range(1, len(rows1)):
    row = rows1[r_idx]
    cells = row.find_all(["th", "td"])
    if len(cells) < 2: continue
    
    year_str = re.sub(r"\[.*?\]", "", cells[0].get_text(strip=True))
    m = re.search(r"^(\d{4})", year_str)
    if not m: continue
    year_val = int(m.group(1))
    
    cell = cells[1]
    
    # Replace <br> and <li> with newlines before getting text
    for br in cell.find_all("br"):
        br.replace_with("\n")
    for li in cell.find_all("li"):
        li.insert_before("\n")
        
    text = cell.get_text("", strip=False)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for line in lines:
        line = re.sub(r"\[[a-z]{2,3}\]", "", line)
        line = re.sub(r"\[\d+\]", "", line)
        
        parts = line.split(":", 1)
        if len(parts) == 2:
            cat = parts[0].strip()
            rest = parts[1].strip()
            
            # Skip if it is Best Film since we already got it from Table 0
            # Wait, Table 0 is Best Film (International), Table 1 might have Best Film (Argentinian)
            # Let's keep it, the ingestion script handles duplicates fine
            
            film = ""
            nominee = ""
            
            if ", for " in rest:
                subparts = rest.split(", for ")
                nominee = subparts[0].strip()
                film = re.sub(r"\(.*?\)", "", subparts[1]).strip()
            elif ", by " in rest:
                subparts = rest.split(", by ")
                film = subparts[0].strip()
                nominee = re.sub(r"\(.*?\)", "", subparts[1]).strip()
            else:
                val = re.sub(r"\(.*?\)", "", rest).strip()
                if "act" in cat.lower() or "direct" in cat.lower():
                    nominee = val
                else:
                    film = val
                    
            if not nominee and not film:
                continue
                
            csv_rows.append({
                "year": year_val,
                "ceremony": "BAFICI Awards",
                "category": cat,
                "nominee": nominee,
                "film": film,
                "won": 1
            })

# Save to CSV
output_path = r"c:\Users\INFOTECH\OneDrive\Desktop\Awardfilms\scripts\bafici_raw.csv"
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["year", "ceremony", "category", "nominee", "film", "won"])
    writer.writeheader()
    writer.writerows(csv_rows)

print(f"Scraped {len(csv_rows)} rows and saved to {output_path}")
