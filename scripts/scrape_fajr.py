import requests
from bs4 import BeautifulSoup
import re
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

pages = [
    ("Best Film", "https://en.wikipedia.org/wiki/Crystal_Simorgh_for_Best_Film"),
    ("Best Director", "https://en.wikipedia.org/wiki/Crystal_Simorgh_for_Best_Director"),
    ("Best Actor", "https://en.wikipedia.org/wiki/Crystal_Simorgh_for_Best_Actor"),
    ("Best Screenplay", "https://en.wikipedia.org/wiki/Crystal_Simorgh_for_Best_Screenplay")
]

headers_req = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
}

csv_rows = []

for category, url in pages:
    r = requests.get(url, headers=headers_req)
    if r.status_code != 200:
        continue
        
    soup = BeautifulSoup(r.text, 'html.parser')
    tables = soup.find_all("table", class_=lambda c: c and "wikitable" in c)
    if not tables:
        continue
        
    # Find the table that has 'year' in headers
    target_table = None
    target_headers = []
    for t in tables:
        tr = t.find("tr")
        if tr:
            h = [th.get_text(strip=True).lower() for th in tr.find_all(["th", "td"])]
            if 'year' in h:
                target_table = t
                target_headers = h
                break
                
    if not target_table:
        continue
        
    # Find indices
    try:
        idx_year = target_headers.index('year')
        idx_film = target_headers.index('film')
        # nominee could be director, actor, producer(s), screenwriter(s)
        idx_nominee = -1
        for i, h in enumerate(target_headers):
            if h in ['director', 'actor', 'producer(s)', 'screenwriter(s)']:
                idx_nominee = i
                break
        
        if idx_nominee == -1:
            print(f"Could not find nominee column for {category}")
            continue
    except ValueError:
        print(f"Could not find required columns for {category}")
        continue
        
    rows = target_table.find_all("tr")
    
    current_year = None
    
    for r_idx in range(1, len(rows)):
        row = rows[r_idx]
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
            
        # check if it's an empty row or just a separator
        texts = [c.get_text(" ", strip=True) for c in cells]
        
        # Check background color for winner
        cell_styles = [c.get('style', '') for c in cells]
        is_winner = any('FAEB86' in s.upper() or 'B0C4DE' in s.upper() for s in cell_styles)
        
        # In some rows, year is present (rowspan). In others it's missing.
        # If the first cell matches a year pattern, it's a year cell
        first_text = texts[0]
        year_match = re.search(r"^(\d{4})", re.sub(r"\[.*?\]", "", first_text))
        
        if year_match and len(texts) > max(idx_film, idx_nominee):
            current_year = int(year_match.group(1))
            val_film = texts[idx_film]
            val_nominee = texts[idx_nominee]
        else:
            # no year cell, so indices are shifted by -1
            if current_year is None:
                continue
            if len(texts) > max(idx_film-1, idx_nominee-1):
                val_film = texts[idx_film-1]
                val_nominee = texts[idx_nominee-1]
            else:
                continue
                
        val_film = re.sub(r"\[.*?\]", "", val_film).strip()
        val_nominee = re.sub(r"\[.*?\]", "", val_nominee).strip()
        
        # some rows have "Not awarded" or "No winner"
        if "not awarded" in val_film.lower() or "no winner" in val_film.lower() or "no absolute winner" in val_film.lower():
            continue
            
        if not val_film and not val_nominee:
            continue
            
        csv_rows.append({
            "year": current_year,
            "ceremony": "Crystal Simorgh Awards",
            "category": category,
            "nominee": val_nominee,
            "film": val_film,
            "won": 1 if is_winner else 0
        })

output_path = r"c:\Users\INFOTECH\OneDrive\Desktop\Awardfilms\scripts\fajr_raw.csv"
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["year", "ceremony", "category", "nominee", "film", "won"])
    writer.writeheader()
    writer.writerows(csv_rows)

print(f"Scraped {len(csv_rows)} rows and saved to {output_path}")
