import requests
from bs4 import BeautifulSoup
import re
import csv
import os

def parse_html_table(table):
    rows = table.find_all("tr")
    num_rows = len(rows)
    if num_rows == 0:
        return []
    
    # Calculate max columns
    num_cols = 0
    for r in rows:
        cells = r.find_all(["td", "th"])
        col_count = 0
        for c in cells:
            col_count += int(c.get("colspan", 1))
        if col_count > num_cols:
            num_cols = col_count
            
    grid = [[None for _ in range(num_cols)] for _ in range(num_rows)]
    
    for r_idx, r in enumerate(rows):
        cells = r.find_all(["td", "th"])
        c_idx = 0
        for cell in cells:
            while c_idx < num_cols and grid[r_idx][c_idx] is not None:
                c_idx += 1
                
            rowspan = int(cell.get("rowspan", 1))
            colspan = int(cell.get("colspan", 1))
            
            val = cell.get_text(" ", strip=True)
            
            # Winner detection
            is_winner = False
            style = cell.get("style", "")
            bg = cell.get("bgcolor", "")
            style_lower = style.lower()
            bg_lower = bg.lower()
            
            winner_colors = ["#faeb86", "#b0c4de", "rgb(250, 235, 134)", "rgb(176, 196, 222)"]
            if any(color in style_lower for color in winner_colors) or any(color in bg_lower for color in winner_colors):
                is_winner = True
            
            parent_style = cell.parent.get("style", "").lower()
            if any(color in parent_style for color in winner_colors):
                is_winner = True
                
            cell_data = {
                "text": val,
                "is_winner": is_winner,
            }
            
            for r_offset in range(rowspan):
                for c_offset in range(colspan):
                    if r_idx + r_offset < num_rows and c_idx + c_offset < num_cols:
                        grid[r_idx + r_offset][c_idx + c_offset] = cell_data
                        
            c_idx += colspan
            
    return grid

urls = {
    "Best Film": "https://pt.wikipedia.org/wiki/Pr%C3%AAmio_Grande_Otelo_de_Melhor_Longa-metragem_de_Fic%C3%A7%C3%A3o",
    "Best Director": "https://pt.wikipedia.org/wiki/Pr%C3%AAmio_Grande_Otelo_de_Melhor_Dire%C3%A7%C3%A3o",
    "Best Actor": "https://pt.wikipedia.org/wiki/Pr%C3%AAmio_Grande_Otelo_de_Melhor_Ator",
    "Best Actress": "https://pt.wikipedia.org/wiki/Pr%C3%AAmio_Grande_Otelo_de_Melhor_Atriz"
}

tables_to_process = {
    "Best Film": [0, 1, 2],
    "Best Director": [0, 1, 2],
    "Best Actor": [0],
    "Best Actress": [0]
}

headers_req = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

csv_rows = []

for category_name, url in urls.items():
    print(f"Scraping category: {category_name}...")
    r = requests.get(url, headers=headers_req)
    if r.status_code != 200:
        print(f"Failed to fetch {url}, status code: {r.status_code}")
        continue
        
    soup = BeautifulSoup(r.text, 'html.parser')
    tables = soup.find_all("table", class_=lambda c: c and "wikitable" in c)
    target_tables = tables_to_process[category_name]
    
    for t_idx in target_tables:
        if t_idx >= len(tables):
            continue
        t = tables[t_idx]
        grid = parse_html_table(t)
        if not grid or len(grid) < 2:
            continue
            
        headers = [cell['text'].lower() if cell else '' for cell in grid[0]]
        
        # Map headers
        year_idx = -1
        film_idx = -1
        nominee_idx = -1
        
        for idx, h in enumerate(headers):
            if 'ano' in h or 'cerim' in h:
                year_idx = idx
            elif 'filme' in h or 'trabalho' in h:
                film_idx = idx
            elif 'diretor' in h or 'ator' in h or 'atriz' in h:
                nominee_idx = idx
                
        # Fallbacks for specific categories
        if category_name == "Best Film" and film_idx == -1:
            film_idx = 1
        if category_name == "Best Director" and nominee_idx == -1:
            nominee_idx = 1
            film_idx = 2
            
        current_year = None
        
        for r_idx in range(1, len(grid)):
            row = grid[r_idx]
            if not row:
                continue
                
            # Get raw texts
            texts = [cell['text'] if cell else '' for cell in row]
            
            # Skip if it is a subheader/empty row
            if len(texts) < 2 or all(not val for val in texts):
                continue
                
            # Extract Year
            year_val = current_year
            if year_idx != -1 and year_idx < len(texts) and texts[year_idx]:
                y_clean = re.sub(r"\[.*?\]", "", texts[year_idx]).strip()
                m = re.search(r"^(\d{4})", y_clean)
                if m:
                    year_val = int(m.group(1))
                    current_year = year_val
                    
            if not year_val:
                # For Best Director, there is a subheader row that only contains the year (e.g. '2002')
                # If length is 1 or rest is empty, check if texts[0] looks like a year
                if len(texts) == 1 or (len(texts) >= 2 and all(not val for val in texts[1:])):
                    y_clean = re.sub(r"\[.*?\]", "", texts[0]).strip()
                    m = re.search(r"^(\d{4})", y_clean)
                    if m:
                        current_year = int(m.group(1))
                continue
                
            # For Best Director, if nominee is empty, it could be a year subheader
            if nominee_idx != -1 and nominee_idx < len(texts) and not texts[nominee_idx]:
                continue
                
            # Extract Film and Nominee
            film_val = ""
            if film_idx != -1 and film_idx < len(texts):
                film_val = re.sub(r"\[.*?\]", "", texts[film_idx]).strip()
                
            nominee_val = ""
            if nominee_idx != -1 and nominee_idx < len(texts):
                nominee_val = re.sub(r"\[.*?\]", "", texts[nominee_idx]).strip()
                
            # Detect Win
            is_winner = any(cell['is_winner'] if cell else False for cell in row)
            
            # Clean up nominee/film
            film_val = film_val.strip('"').strip("'").strip()
            nominee_val = nominee_val.strip('"').strip("'").strip()
            
            # Skip if both are empty
            if not film_val and not nominee_val:
                continue
                
            csv_rows.append({
                "year": year_val,
                "ceremony": "Grande Prêmio do Cinema Brasileiro",
                "category": category_name,
                "nominee": nominee_val,
                "film": film_val if film_val else nominee_val,
                "won": 1 if is_winner else 0
            })

# Save to CSV
output_path = r"C:\Users\INFOTECH\OneDrive\Desktop\Awardfilms\scripts\grande_otelo_raw.csv"
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["year", "ceremony", "category", "nominee", "film", "won"])
    writer.writeheader()
    writer.writerows(csv_rows)

print(f"Scraped {len(csv_rows)} rows and saved to {output_path}")
