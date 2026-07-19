import requests
from bs4 import BeautifulSoup
import re
import csv

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
    row_styles = []
    
    for r_idx, r in enumerate(rows):
        cells = r.find_all(["td", "th"])
        c_idx = 0
        
        style = r.get("style", "")
        bg = r.get("bgcolor", "")
        row_styles.append(style + " " + bg)
        
        for cell in cells:
            while c_idx < num_cols and grid[r_idx][c_idx] is not None:
                c_idx += 1
                
            rowspan = int(cell.get("rowspan", 1))
            colspan = int(cell.get("colspan", 1))
            
            val = cell.get_text(" ", strip=True)
            cell_style = cell.get("style", "")
            cell_bg = cell.get("bgcolor", "")
            
            for r_offset in range(rowspan):
                for c_offset in range(colspan):
                    if r_idx + r_offset < num_rows and c_idx + c_offset < num_cols:
                        grid[r_idx + r_offset][c_idx + c_offset] = {
                            "text": val,
                            "style": cell_style + " " + cell_bg,
                            "is_original_to_row": (r_offset == 0)
                        }
                        
            c_idx += colspan
            
    return grid, row_styles

urls = {
    "Best Film": "https://es.wikipedia.org/wiki/Anexo:Premio_Sur_a_la_mejor_pel%C3%ADcula",
    "Best Director": "https://es.wikipedia.org/wiki/Anexo:Premio_Sur_a_la_mejor_direcci%C3%B3n",
    "Best Actor": "https://es.wikipedia.org/wiki/Anexo:Premio_Sur_al_mejor_actor",
    "Best Actress": "https://es.wikipedia.org/wiki/Anexo:Premio_Sur_a_la_mejor_actriz"
}

headers_req = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

csv_rows = []

for category_name, url in urls.items():
    r = requests.get(url, headers=headers_req)
    soup = BeautifulSoup(r.text, 'html.parser')
    tables = soup.find_all("table", class_=lambda c: c and "wikitable" in c)
    
    for t in tables:
        grid, row_styles = parse_html_table(t)
        if not grid or len(grid) < 2:
            continue
            
        headers = [cell['text'].lower() if cell else '' for cell in grid[0]]
        if not any(h in headers for h in ['edición', 'película', 'dirección', 'director', 'actor', 'actriz']):
            continue
            
        year_idx = -1
        film_idx = -1
        nominee_idx = -1
        
        for idx, h in enumerate(headers):
            if 'edici' in h or 'año' in h or 'cerim' in h:
                year_idx = idx
            elif 'película' in h or 'obra' in h:
                film_idx = idx
            elif 'director' in h or 'dirección' in h or 'actor' in h or 'actriz' in h:
                nominee_idx = idx
                
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
                
            texts = [cell['text'] if cell else '' for cell in row]
            if len(texts) < 2 or all(not val for val in texts):
                continue
                
            year_val = current_year
            if year_idx != -1 and year_idx < len(texts) and texts[year_idx]:
                y_clean = re.sub(r"\[.*?\]", "", texts[year_idx]).strip()
                m = re.search(r"^(\d{4})", y_clean)
                if m:
                    year_val = int(m.group(1))
                    current_year = year_val
                    
            if not year_val:
                if len(texts) == 1 or (len(texts) >= 2 and all(not val for val in texts[1:])):
                    y_clean = re.sub(r"\[.*?\]", "", texts[0]).strip()
                    m = re.search(r"^(\d{4})", y_clean)
                    if m:
                        current_year = int(m.group(1))
                continue
                
            if nominee_idx != -1 and nominee_idx < len(texts) and not texts[nominee_idx]:
                continue
                
            film_val = ""
            if film_idx != -1 and film_idx < len(texts):
                film_val = re.sub(r"\[.*?\]", "", texts[film_idx]).strip()
                
            nominee_val = ""
            if nominee_idx != -1 and nominee_idx < len(texts):
                nominee_val = re.sub(r"\[.*?\]", "", texts[nominee_idx]).strip()
                
            is_winner = False
            winner_colors = ["#faeb86", "#b0c4de", "yellow", "gold", "khaki", "#f0e68c"]
            
            r_style = row_styles[r_idx].lower()
            if any(color in r_style for color in winner_colors):
                is_winner = True
            else:
                for c_idx, cell in enumerate(row):
                    if c_idx == year_idx or cell is None or not cell.get("is_original_to_row", False):
                        continue
                    c_style = cell.get("style", "").lower()
                    if any(color in c_style for color in winner_colors):
                        is_winner = True
                        break
            
            film_val = film_val.strip('"').strip("'").strip()
            nominee_val = nominee_val.strip('"').strip("'").strip()
            
            if not film_val and not nominee_val:
                continue
                
            csv_rows.append({
                "year": year_val,
                "ceremony": "Premios Sur",
                "category": category_name,
                "nominee": nominee_val,
                "film": film_val if film_val else nominee_val,
                "won": 1 if is_winner else 0
            })

# Save to CSV
output_path = r"c:\Users\INFOTECH\OneDrive\Desktop\Awardfilms\scripts\sur_raw.csv"
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["year", "ceremony", "category", "nominee", "film", "won"])
    writer.writeheader()
    writer.writerows(csv_rows)

print(f"Scraped {len(csv_rows)} rows and saved to {output_path}")
