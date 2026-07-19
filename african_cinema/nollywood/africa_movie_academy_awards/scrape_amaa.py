import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configurations
TOR_SOCKS_PORT = 9050
HEADERS = {
    "User-Agent": "MultiThreadAMAAScraper/1.0 (educational data science project; contact: student_scraper@example.com)"
}

AMAA_CATEGORIES = [
    {"category": "Best Film", "wiki": "Africa_Movie_Academy_Award_for_Best_Film"},
    {"category": "Best Director", "wiki": "Africa_Movie_Academy_Award_for_Best_Director"},
    {"category": "Best Actor in a Leading Role", "wiki": "Africa_Movie_Academy_Award_for_Best_Actor_in_a_Leading_Role"},
    {"category": "Best Actress in a Leading Role", "wiki": "Africa_Movie_Academy_Award_for_Best_Actress_in_a_Leading_Role"},
    {"category": "Best Actor in a Supporting Role", "wiki": "Africa_Movie_Academy_Award_for_Best_Actor_in_a_Supporting_Role"},
    {"category": "Best Actress in a Supporting Role", "wiki": "Africa_Movie_Academy_Award_for_Best_Actress_in_a_Supporting_Role"},
    {"category": "Best Animation", "wiki": "Africa_Movie_Academy_Award_for_Best_Animation"},
    {"category": "Best Cinematography", "wiki": "Africa_Movie_Academy_Award_for_Best_Cinematography"},
    {"category": "Best Costume Design", "wiki": "Africa_Movie_Academy_Award_for_Best_Costume_Design"},
    {"category": "Best Diaspora Documentary", "wiki": "Africa_Movie_Academy_Award_for_Best_Diaspora_Documentary"},
    {"category": "Best Diaspora Feature", "wiki": "Africa_Movie_Academy_Award_for_Best_Diaspora_Feature"},
    {"category": "Best Documentary", "wiki": "Africa_Movie_Academy_Award_for_Best_Documentary"},
    {"category": "Best Editing", "wiki": "Africa_Movie_Academy_Award_for_Best_Editing"},
    {"category": "Best Film by an African Living Abroad", "wiki": "Africa_Movie_Academy_Award_for_Best_Film_by_an_African_Living_Abroad"},
    {"category": "Best Film in an African Language", "wiki": "Africa_Movie_Academy_Award_for_Best_Film_in_an_African_Language"},
    {"category": "Best Makeup", "wiki": "Africa_Movie_Academy_Award_for_Best_Makeup"},
    {"category": "Best Nigerian Film", "wiki": "Africa_Movie_Academy_Award_for_Best_Nigerian_Film"},
    {"category": "Best Production Design", "wiki": "Africa_Movie_Academy_Award_for_Best_Production_Design"},
    {"category": "Best Screenplay", "wiki": "Africa_Movie_Academy_Award_for_Best_Screenplay"},
    {"category": "Best Short Film", "wiki": "Africa_Movie_Academy_Award_for_Best_Short_Film"},
    {"category": "Best Sound", "wiki": "Africa_Movie_Academy_Award_for_Best_Sound"},
    {"category": "Best Soundtrack", "wiki": "Africa_Movie_Academy_Award_for_Best_Soundtrack"},
    {"category": "Best Visual Effects", "wiki": "Africa_Movie_Academy_Award_for_Best_Visual_Effects"},
    {"category": "Most Promising Actor", "wiki": "Africa_Movie_Academy_Award_for_Most_Promising_Actor"}
]

def check_stream_ip(thread_proxies, thread_id):
    """Verifies and displays the isolated Tor IP allocated to this specific thread stream."""
    try:
        ip = requests.get("https://icanhazip.com", proxies=thread_proxies, timeout=15).text.strip()
        print(f"[Thread {thread_id}] Active Tor Stream IP -> {ip}")
    except Exception:
        print(f"[Thread {thread_id}] Proxy tunnel active, continuing data extraction...")

def clean_text(text):
    if not text:
        return ""
    # Remove citation brackets like [1], [2], [Note 1]
    text = re.sub(r'\[[^\]]+\]', '', text)
    # Remove helper symbols
    text = text.replace('†', '').replace('*', '').replace('‡', '')
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_html_table_to_grid(table):
    """Parses an HTML table into a grid list of lists to handle rowspans and colspans."""
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
        return "Africa Movie Academy Awards"
    edition_num = year - 2004
    if edition_num <= 0:
        return "Africa Movie Academy Awards"
    if 11 <= edition_num % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(edition_num % 10, "th")
    return f"{edition_num}{suffix} Africa Movie Academy Awards"

def is_valid_award_table(headers_list):
    # Must contain 'year' or 'date'
    has_year = any("year" in h or "date" in h for h in headers_list)
    # Must contain some sort of nominee representation
    has_nominee = any(
        any(x in h for x in ("film", "movie", "title", "actor", "actress", "director", "nominee", "recipient", "winner", "name", "performer", "writer", "recipient"))
        for h in headers_list
    )
    # Must NOT look like a ceremony overview table
    is_ceremony_overview = any("venue" in h or "host" in h or "city" in h or "ceremony date" in h or "location" in h for h in headers_list)
    
    return has_year and has_nominee and not is_ceremony_overview

def parse_category_page(html, category_name, source_url):
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table", class_=re.compile("wikitable"))
    
    records = []
    for t_idx, table in enumerate(tables):
        grid = parse_html_table_to_grid(table)
        if not grid:
            continue
            
        # Detect headers
        header_idx = None
        for r_idx, row in enumerate(grid):
            row_texts = [clean_text(cell.get_text() if cell else "").lower() for cell in row]
            if any("year" in cell_text for cell_text in row_texts):
                header_idx = r_idx
                break
                
        if header_idx is None:
            continue
            
        headers_list = [clean_text(cell.get_text() if cell else "").lower() for cell in grid[header_idx]]
        
        if not is_valid_award_table(headers_list):
            continue
            
        # Column indices
        year_col = next((i for i, h in enumerate(headers_list) if "year" in h), 0)
        film_col = next((i for i, h in enumerate(headers_list) if "film" in h or "movie" in h or "title" in h), None)
        person_col = next((i for i, h in enumerate(headers_list) if any(x in h for x in ("recipient", "winner", "director", "actor", "actress", "nominee", "name", "performer", "writer"))), None)
        result_col = next((i for i, h in enumerate(headers_list) if any(x in h for x in ("result", "status", "outcome"))), None)
        
        current_year = None
        for r_idx in range(header_idx + 1, len(grid)):
            row_cells = grid[r_idx]
            if not row_cells:
                continue
                
            # Extract year
            year_cell = row_cells[year_col] if year_col < len(row_cells) else None
            year_text = clean_text(year_cell.get_text() if year_cell else "")
            year_match = re.search(r'\b(20\d{2}|19\d{2})\b', year_text)
            if year_match:
                current_year = int(year_match.group(1))
                
            if not current_year:
                continue
                
            film = ""
            nominee = ""
            
            if film_col is not None and film_col < len(row_cells):
                film = clean_text(row_cells[film_col].get_text() if row_cells[film_col] else "")
            if person_col is not None and person_col < len(row_cells):
                nominee = clean_text(row_cells[person_col].get_text() if row_cells[person_col] else "")
                
            # Fallback mappings
            if not nominee and film:
                nominee = film
            elif not film and nominee:
                film = "N/A"
                
            if not film and not nominee:
                continue
                
            # Skip repeating headers inside the table
            if film.lower() in ("film", "title", "movie") or nominee.lower() in ("recipient", "winner", "director", "actor", "actress"):
                continue
                
            # Winner detection
            is_winner = False
            if result_col is not None and result_col < len(row_cells):
                res_cell = row_cells[result_col]
                if res_cell:
                    res_text = clean_text(res_cell.get_text()).lower()
                    if "won" in res_text or "winner" in res_text:
                        is_winner = True
                    elif "nominated" in res_text or "nominee" in res_text:
                        is_winner = False
            else:
                # styling/formatting checks
                cell_to_check = row_cells[person_col] if person_col is not None else row_cells[film_col]
                if cell_to_check:
                    c_style = (cell_to_check.get("style") or "").lower()
                    c_bg = (cell_to_check.get("bgcolor") or "").lower()
                    row_style = (cell_to_check.parent.get("style") or "").lower() if cell_to_check.parent else ""
                    row_bg = (cell_to_check.parent.get("bgcolor") or "").lower() if cell_to_check.parent else ""
                    
                    has_highlight = False
                    for style_str in (c_style, c_bg, row_style, row_bg):
                        if style_str and not any(w in style_str for w in ("fff", "ffffff", "transparent", "inherit")):
                            if any(x in style_str for x in ("faeb86", "9eff9e", "gold", "yellow", "green")):
                                has_highlight = True
                                
                    if has_highlight:
                        is_winner = True
                    elif cell_to_check.find("b") or cell_to_check.name == "th":
                        is_winner = True
                        
            records.append({
                "year": current_year,
                "ceremony": get_ceremony_name(current_year),
                "category": category_name,
                "nominee": nominee,
                "film": film,
                "winner": 1 if is_winner else 0,
                "source_url": source_url
            })
            
    return records

def scrape_page_worker(cat_info, thread_id):
    category_name = cat_info["category"]
    wiki_path = cat_info["wiki"]
    url = f"https://en.wikipedia.org/wiki/{wiki_path}"
    
    socks_user = f"thread_user_{thread_id}"
    socks_pass = f"thread_secret_{thread_id}"
    
    thread_proxies = {
        "http": f"socks5h://{socks_user}:{socks_pass}@127.0.0.1:{TOR_SOCKS_PORT}",
        "https": f"socks5h://{socks_user}:{socks_pass}@127.0.0.1:{TOR_SOCKS_PORT}",
    }
    
    time.sleep(random.uniform(0.5, 2.0))
    check_stream_ip(thread_proxies, thread_id)
    
    try:
        print(f"[Thread {thread_id}] Fetching {category_name} from {url}...")
        response = requests.get(url, headers=HEADERS, proxies=thread_proxies, timeout=30)
        if response.status_code == 200:
            recs = parse_category_page(response.text, category_name, url)
            print(f"[Thread {thread_id}] Successfully parsed {len(recs)} records for {category_name}")
            return recs
        else:
            print(f"[Thread {thread_id}] HTTP error {response.status_code} for {category_name}")
            return []
    except Exception as e:
        print(f"[Thread {thread_id}] Error parsing {category_name}: {e}")
        return []

def main():
    combined_results = []
    
    print("[*] Starting multithreaded AMAA scraping run...")
    print(f"[*] Port target: {TOR_SOCKS_PORT} (Enforcing SOCKS5 credentials stream isolation)")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for index, cat_info in enumerate(AMAA_CATEGORIES):
            futures.append(executor.submit(scrape_page_worker, cat_info, index))
            
        for future in as_completed(futures):
            combined_results.extend(future.result())

    # Dedup and sort data
    df = pd.DataFrame(combined_results)
    if not df.empty:
        # Sort by year, category, winner (descending, so winner=1 is first), nominee
        df = df.sort_values(by=["year", "category", "winner", "nominee"], ascending=[True, True, False, True])
        df = df.drop_duplicates(subset=["year", "category", "nominee", "film"])
        
        import csv
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_file_path = os.path.join(output_dir, "amaa_awards.csv")
        df.to_csv(output_file_path, index=False, quoting=csv.QUOTE_MINIMAL)
        
        print(f"\nDone! Consolidate AMAA database saved to: {output_file_path}")
        print(f"Total Unique Nominations Scraped & Saved: {len(df)}")
        print(df.head())
    else:
        print("\nERROR: No records were scraped.")

if __name__ == "__main__":
    main()
