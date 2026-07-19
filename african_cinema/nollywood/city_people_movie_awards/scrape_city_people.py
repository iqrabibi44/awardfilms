import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re

TOR_SOCKS_PORT = 9050
HEADERS = {
    "User-Agent": "MultiThreadCityPeopleScraper/1.0 (educational data science project; contact: student_scraper@example.com)"
}
URL = "https://en.wikipedia.org/wiki/City_People_Entertainment_Awards"

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\[[^\]]+\]', '', text)
    text = text.replace('†', '').replace('*', '').replace('‡', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_html_table_to_grid(table):
    rows = table.find_all("tr")
    if not rows:
        return []
    
    grid = {}
    max_c = 0
    max_r = len(rows)
    
    for r_idx, row in enumerate(rows):
        cells = row.find_all(["td", "th"])
        c_idx = 0
        for cell in cells:
            while (r_idx, c_idx) in grid:
                c_idx += 1
            
            rowspan = int(cell.get("rowspan", 1))
            colspan = int(cell.get("colspan", 1))
            
            for dr in range(rowspan):
                for dc in range(colspan):
                    grid[(r_idx + dr, c_idx + dc)] = cell
            
            c_idx += colspan
            if c_idx > max_c:
                max_c = c_idx
                
    table_grid = []
    for r in range(max_r):
        row_cells = []
        for c in range(max_c):
            row_cells.append(grid.get((r, c), None))
        table_grid.append(row_cells)
        
    return table_grid

def main():
    print("[*] Starting City People Awards scraping run...")
    
    thread_proxies = {
        "http": f"socks5h://thread_cp:secret@127.0.0.1:{TOR_SOCKS_PORT}",
        "https": f"socks5h://thread_cp:secret@127.0.0.1:{TOR_SOCKS_PORT}",
    }
    
    try:
        response = requests.get(URL, headers=HEADERS, proxies=thread_proxies, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        return
        
    soup = BeautifulSoup(response.text, "lxml")
    tables = soup.find_all("table", class_=re.compile("wikitable"))
    
    records = []
    for table_idx, table in enumerate(tables):
        grid = parse_html_table_to_grid(table)
        if not grid:
            continue
            
        category = "General"
        current_year = None
        
        for r_idx, row_cells in enumerate(grid):
            # Check for empty rows
            non_empty_cells = [cell for cell in row_cells if cell is not None]
            if not non_empty_cells:
                continue
                
            # Get unique cells in the row
            unique_cells = []
            for cell in non_empty_cells:
                if cell not in unique_cells:
                    unique_cells.append(cell)
                    
            # 1. If row has only 1 unique cell (category block heading)
            if len(unique_cells) == 1:
                cat_text = clean_text(unique_cells[0].get_text())
                if cat_text and cat_text.lower() not in ("year", "recipient", "result", "status", "category", "recipient(s) and nominee(s)"):
                    category = cat_text
                continue
                
            # 2. Check if this is a header row (e.g. contains 'Year', 'Recipient', 'Result')
            row_texts = [clean_text(cell.get_text() if cell else "").lower() for cell in row_cells]
            if any(h in row_texts for h in ("year", "recipient", "result", "status", "recipient(s) and nominee(s)")):
                continue
                
            # 3. Parse nominee row
            # Column 0: Year
            # Column 1: Recipient
            # Column 2: Result
            year_cell = row_cells[0] if len(row_cells) > 0 else None
            recip_cell = row_cells[1] if len(row_cells) > 1 else None
            result_cell = row_cells[2] if len(row_cells) > 2 else None
            
            year_text = clean_text(year_cell.get_text() if year_cell else "")
            year_match = re.search(r'\b(20\d{2}|19\d{2})\b', year_text)
            if year_match:
                current_year = int(year_match.group(1))
                
            if not current_year:
                continue
                
            nominee_text = clean_text(recip_cell.get_text() if recip_cell else "")
            if not nominee_text:
                continue
                
            # Split recipient text into nominee and film/song (e.g. HarrySong – "Reggae Blues")
            nominee = nominee_text
            film = category
            
            dash_match = re.search(r'^(.*?)\s*[–\—\-]\s*(.*?)$', nominee_text)
            if dash_match:
                nominee = clean_text(dash_match.group(1))
                film = clean_text(dash_match.group(2)).strip('"\'')
                
            is_winner = False
            if result_cell:
                res_text = clean_text(result_cell.get_text()).lower()
                if "won" in res_text or "winner" in res_text:
                    is_winner = True
                    
            ceremony_num = current_year - 2008
            if ceremony_num <= 0:
                ceremony_name = "City People Entertainment Awards"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(ceremony_num % 10, "th")
                if 11 <= ceremony_num % 100 <= 13:
                    suffix = "th"
                ceremony_name = f"{ceremony_num}{suffix} City People Entertainment Awards"
                
            records.append({
                "year": current_year,
                "ceremony": ceremony_name,
                "category": category,
                "nominee": nominee,
                "film": film,
                "winner": 1 if is_winner else 0,
                "source_url": URL
            })
            
    df = pd.DataFrame(records)
    if not df.empty:
        df = df.sort_values(by=["year", "category", "winner", "nominee"], ascending=[True, True, False, True])
        df = df.drop_duplicates(subset=["year", "category", "nominee", "film"])
        
        import csv
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_file_path = os.path.join(output_dir, "city_people_awards.csv")
        df.to_csv(output_file_path, index=False, quoting=csv.QUOTE_MINIMAL)
        print(f"[+] City People data saved to: {output_file_path}")
        print(f"Total Unique Winners/Nominees Scraped: {len(df)}")
    else:
        print("[-] ERROR: No City People records scraped.")

if __name__ == "__main__":
    main()
