import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
import random

TOR_SOCKS_PORT = 9050
HEADERS = {
    "User-Agent": "MultiThreadAFRIFFScraper/1.0 (educational data science project; contact: student_scraper@example.com)"
}
URL = "https://en.wikipedia.org/wiki/Africa_International_Film_Festival"

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

def get_ceremony_name(year):
    if not year:
        return "Africa International Film Festival"
    # Mapping years:
    edition_map = {
        2010: 1, 2011: 2, 2013: 3, 2014: 4, 2015: 5, 2016: 6, 2017: 7, 2018: 8, 2019: 9, 2021: 10
    }
    edition_num = edition_map.get(year, year - 2009)
    if edition_num <= 0:
        return "Africa International Film Festival"
    if 11 <= edition_num % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(edition_num % 10, "th")
    return f"{edition_num}{suffix} Africa International Film Festival"

def main():
    print("[*] Starting AFRIFF scraping run...")
    
    thread_proxies = {
        "http": f"socks5h://thread_afriff:secret@127.0.0.1:{TOR_SOCKS_PORT}",
        "https": f"socks5h://thread_afriff:secret@127.0.0.1:{TOR_SOCKS_PORT}",
    }
    
    try:
        response = requests.get(URL, headers=HEADERS, proxies=thread_proxies, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        return
        
    soup = BeautifulSoup(response.text, "lxml")
    records = []
    
    tables = soup.find_all("table", class_=re.compile("wikitable"))
    for idx, table in enumerate(tables):
        # Look backwards for heading containing year
        prev_h = table.find_previous(["h2", "h3", "h4"])
        year = None
        while prev_h:
            prev_text = prev_h.get_text()
            year_match = re.search(r'\b(20\d{2})\b', prev_text)
            if year_match:
                year = int(year_match.group(1))
                break
            prev_h = prev_h.find_previous(["h2", "h3", "h4"])
            
        if not year:
            print(f"[-] Skipping table {idx}: Year not found.")
            continue
            
        ceremony_name = get_ceremony_name(year)
        grid = parse_html_table_to_grid(table)
        if not grid:
            continue
            
        # Detect columns
        header_idx = None
        for r_idx, row in enumerate(grid):
            row_texts = [clean_text(cell.get_text() if cell else "").lower() for cell in row]
            if any("award" in cell_text or "winner" in cell_text or "category" in cell_text for cell_text in row_texts):
                header_idx = r_idx
                break
                
        if header_idx is None:
            continue
            
        headers_list = [clean_text(cell.get_text() if cell else "").lower() for cell in grid[header_idx]]
        award_col = next((i for i, h in enumerate(headers_list) if "award" in h or "category" in h), 0)
        winner_col = next((i for i, h in enumerate(headers_list) if "winner" in h or "recipient" in h), 1 if len(headers_list) > 1 else 0)
        
        for r_idx in range(header_idx + 1, len(grid)):
            row_cells = grid[r_idx]
            if not row_cells:
                continue
                
            award_cell = row_cells[award_col] if award_col < len(row_cells) else None
            winner_cell = row_cells[winner_col] if winner_col < len(row_cells) else None
            
            category = clean_text(award_cell.get_text() if award_cell else "")
            winner_text = clean_text(winner_cell.get_text() if winner_cell else "")
            
            if not category or category.lower() in ("award", "category", "winner", "recipient"):
                continue
            if not winner_text or winner_text.lower() in ("no award", "none", "n/a"):
                continue
                
            film = winner_text
            nominee = winner_text
            
            by_match = re.search(r'^(.*?)\s+by\s+(.*?)(?:\s*\(.*\))?$', winner_text, re.IGNORECASE)
            if by_match:
                film = clean_text(by_match.group(1))
                nominee = clean_text(by_match.group(2))
            else:
                paren_match = re.search(r'^(.*?)\s*\((.*?)\)$', winner_text)
                if paren_match:
                    film = clean_text(paren_match.group(1))
                    nominee = film
                    
            records.append({
                "year": year,
                "ceremony": ceremony_name,
                "category": category,
                "nominee": nominee,
                "film": film,
                "winner": 1,
                "source_url": URL
            })
            
    df = pd.DataFrame(records)
    if not df.empty:
        df = df.sort_values(by=["year", "category", "nominee"], ascending=[True, True, True])
        df = df.drop_duplicates(subset=["year", "category", "nominee", "film"])
        
        import csv
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_file_path = os.path.join(output_dir, "afriff_awards.csv")
        df.to_csv(output_file_path, index=False, quoting=csv.QUOTE_MINIMAL)
        print(f"[+] AFRIFF data saved to: {output_file_path}")
        print(f"Total Unique Winners Scraped: {len(df)}")
    else:
        print("[-] ERROR: No AFRIFF records scraped.")

if __name__ == "__main__":
    main()
