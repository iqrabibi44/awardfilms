import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

TOR_SOCKS_PORT = 9050
HEADERS = {
    "User-Agent": "MultiThreadNEAScraper/1.0 (educational data science project; contact: student_scraper@example.com)"
}

NEA_CEREMONIES = [
    {"year": 2009, "wiki": "2009_Nigeria_Entertainment_Awards", "name": "4th Nigeria Entertainment Awards"},
    {"year": 2010, "wiki": "2010_Nigeria_Entertainment_Awards", "name": "5th Nigeria Entertainment Awards"},
    {"year": 2011, "wiki": "2011_Nigeria_Entertainment_Awards", "name": "6th Nigeria Entertainment Awards"},
    {"year": 2012, "wiki": "2012_Nigeria_Entertainment_Awards", "name": "7th Nigeria Entertainment Awards"},
    {"year": 2013, "wiki": "2013_Nigeria_Entertainment_Awards", "name": "8th Nigeria Entertainment Awards"},
    {"year": 2014, "wiki": "2014_Nigeria_Entertainment_Awards", "name": "9th Nigeria Entertainment Awards"},
    {"year": 2015, "wiki": "2015_Nigeria_Entertainment_Awards", "name": "10th Nigeria Entertainment Awards"},
    {"year": 2016, "wiki": "2016_Nigeria_Entertainment_Awards", "name": "11th Nigeria Entertainment Awards"}
]

def check_stream_ip(thread_proxies, thread_id):
    try:
        ip = requests.get("https://icanhazip.com", proxies=thread_proxies, timeout=15).text.strip()
        print(f"[Thread {thread_id}] Active Tor Stream IP -> {ip}")
    except Exception:
        pass

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\[[^\]]+\]', '', text)
    text = text.replace('†', '').replace('*', '').replace('‡', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_film_and_nominee_element(elem):
    el_copy = BeautifulSoup(str(elem), "lxml")
    for tag in el_copy.find_all(["ul", "ol"]):
        tag.decompose()
    for tag in el_copy.find_all(["sup", "span"]):
        tag.decompose()
        
    i_tags = el_copy.find_all("i")
    if i_tags:
        film_candidate = clean_text(i_tags[0].get_text())
        for i_t in el_copy.find_all("i"):
            i_t.decompose()
        rest_candidate = clean_text(el_copy.get_text())
        
        film = film_candidate
        nominee = rest_candidate
        
        if not nominee:
            parts = re.split(r'\s*[–\—\-]\s*', film)
            if len(parts) >= 2:
                film = parts[0]
                nominee = parts[1]
            else:
                nominee = film
        else:
            nominee = re.sub(r'^[–\—\-\s\•\\–\—\xa0]+', '', nominee)
            nominee = re.sub(r'[–\—\-\s\•\\–\—\xa0]+$', '', nominee)
            nominee = clean_text(nominee)
    else:
        text = clean_text(el_copy.get_text())
        text = re.sub(r'^[\*\s\•\\–\—\-\[\]\(\)\xa0]+', '', text)
        parts = re.split(r'\s*[–\—\-]\s*', text)
        if len(parts) >= 2:
            film = parts[0]
            nominee = parts[1]
        else:
            film = text
            nominee = text
            
    return clean_text(nominee), clean_text(film)

def is_winner_li(li_cell):
    if li_cell.find(["b", "strong"]):
        return True
    return False

def get_nominees_from_cell(cell):
    li_items = cell.find_all("li")
    if li_items:
        res = []
        for li in li_items:
            nom, flm = extract_film_and_nominee_element(li)
            is_win = is_winner_li(li)
            if nom or flm:
                res.append((nom, flm, is_win))
        return res
        
    p_items = cell.find_all("p")
    b_items = cell.find_all(["b", "strong"], recursive=False)
    
    res = []
    for b in b_items:
        if b.find(["ul", "ol", "p"]):
            continue
        nom, flm = extract_film_and_nominee_element(b)
        if nom or flm:
            res.append((nom, flm, True))
            
    for p in p_items:
        nom, flm = extract_film_and_nominee_element(p)
        if nom or flm:
            is_win = is_winner_li(p)
            res.append((nom, flm, is_win))
            
    if not res:
        cell_html = str(cell)
        lines = re.split(r'<br\s*/?>', cell_html, flags=re.IGNORECASE)
        if len(lines) <= 1:
            cell_text = cell.get_text()
            lines = [ln.strip() for ln in cell_text.split("\n") if ln.strip()]
            
        for line in lines:
            line_soup = BeautifulSoup(line, "lxml")
            text = clean_text(line_soup.get_text())
            if text and len(text) > 3 and text.lower() not in ("winner", "nominees", "result", "category"):
                nom, flm = extract_film_and_nominee_element(line_soup)
                is_win = is_winner_li(line_soup)
                if nom or flm:
                    res.append((nom, flm, is_win))
                    
    return res

def parse_tables(soup, ceremony_name, year, source_url):
    tables = soup.find_all("table", class_=re.compile("wikitable"))
    records = []
    
    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue
            
        current_categories = []
        for row in rows:
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
                
            if all(cell.name == "th" for cell in cells):
                current_categories = [clean_text(cell.get_text()) for cell in cells]
                continue
                
            for col_idx, cell in enumerate(cells):
                category = None
                nominees_list = get_nominees_from_cell(cell)
                if not nominees_list:
                    continue
                    
                first_nom, first_film, _ = nominees_list[0]
                cell_text = cell.get_text()
                
                prefix_clean = None
                if first_nom and first_nom in cell_text:
                    prefix = cell_text.split(first_nom)[0]
                    prefix_clean = clean_text(prefix)
                elif first_film and first_film in cell_text:
                    prefix = cell_text.split(first_film)[0]
                    prefix_clean = clean_text(prefix)
                    
                if prefix_clean and len(prefix_clean) > 5 and re.search(r'[A-Za-z]', prefix_clean) and prefix_clean.lower() not in ("winner", "nominees", "result", "category"):
                    category = prefix_clean
                    
                if not category and len(cells) == 2:
                    nominees_0 = get_nominees_from_cell(cells[0])
                    nominees_1 = get_nominees_from_cell(cells[1])
                    if nominees_1 and not nominees_0:
                        cat_text = clean_text(cells[0].get_text())
                        if cat_text and len(cat_text) < 120 and cat_text.lower() not in ("winner", "nominees", "result", "category"):
                            if col_idx == 1:
                                category = cat_text
                                nominees_list = nominees_1
                                
                if not category and current_categories and col_idx < len(current_categories):
                    cat_text = current_categories[col_idx]
                    if cat_text and cat_text.lower() not in ("winner", "nominees", "result", "category"):
                        category = cat_text
                        
                if category and nominees_list:
                    for nom, flm, is_win in nominees_list:
                        records.append({
                            "year": year,
                            "ceremony": ceremony_name,
                            "category": category,
                            "nominee": nom,
                            "film": flm,
                            "winner": 1 if is_win else 0,
                            "source_url": source_url
                        })
    return records

def parse_lists(soup, ceremony_name, year, source_url):
    records = []
    exclude_headings = {
        "contents", "ceremony", "presenters", "performers", "references", 
        "external links", "winners and nominees", "history", "venue", 
        "categories", "notes", "lead role", "supporting role", "nominees", 
        "winners", "multiple nominations", "multiple wins", "major categories",
        "special recognition award", "reception", "broadcast", "hosts",
        "nominations", "win", "wins"
    }
    
    headings = soup.find_all(["h2", "h3", "h4"])
    for heading in headings:
        category = clean_text(heading.get_text())
        if not category or category.lower() in exclude_headings or len(category) > 100:
            continue
            
        start_elem = heading
        if heading.parent and heading.parent.name == "div" and any(cls.startswith("mw-heading") for cls in heading.parent.get("class", [])):
            start_elem = heading.parent
            
        sibling = start_elem.next_sibling
        while sibling:
            if sibling.name in ("h2", "h3", "h4") or (sibling.name == "div" and any(cls.startswith("mw-heading") for cls in sibling.get("class", []))):
                break
                
            if sibling.name == "ul":
                li_items = sibling.find_all("li")
                for li in li_items:
                    nom, flm = extract_film_and_nominee_element(li)
                    is_winner = is_winner_li(li)
                    records.append({
                        "year": year,
                        "ceremony": ceremony_name,
                        "category": category,
                        "nominee": nom,
                        "film": flm,
                        "winner": 1 if is_winner else 0,
                        "source_url": source_url
                    })
            sibling = sibling.next_sibling
    return records

def parse_ceremony_page(html, ceremony_name, year, source_url):
    soup = BeautifulSoup(html, "lxml")
    
    table_recs = parse_tables(soup, ceremony_name, year, source_url)
    list_recs = parse_lists(soup, ceremony_name, year, source_url)
    
    return table_recs + list_recs

def scrape_ceremony_worker(c_info, thread_id):
    ceremony_name = c_info["name"]
    year = c_info["year"]
    wiki_path = c_info["wiki"]
    url = f"https://en.wikipedia.org/wiki/{wiki_path}"
    
    socks_user = f"thread_user_{thread_id}"
    socks_pass = f"thread_secret_{thread_id}"
    
    thread_proxies = {
        "http": f"socks5h://{socks_user}:{socks_pass}@127.0.0.1:{TOR_SOCKS_PORT}",
        "https": f"socks5h://{socks_user}:{socks_pass}@127.0.0.1:{TOR_SOCKS_PORT}",
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if attempt == 0:
                time.sleep(random.uniform(0.5, 2.0))
                check_stream_ip(thread_proxies, thread_id)
                
            print(f"[Thread {thread_id}] Fetching {ceremony_name} ({year})... Attempt {attempt+1}")
            response = requests.get(url, headers=HEADERS, proxies=thread_proxies, timeout=45)
            if response.status_code == 200:
                recs = parse_ceremony_page(response.text, ceremony_name, year, url)
                print(f"[Thread {thread_id}] Successfully parsed {len(recs)} records for {ceremony_name}")
                return recs
            else:
                print(f"[Thread {thread_id}] HTTP error {response.status_code} for {ceremony_name} on attempt {attempt+1}")
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"[Thread {thread_id}] Final error parsing {ceremony_name}: {e}")
            else:
                time.sleep(random.uniform(1.0, 3.0))
                
    return []

def main():
    combined_results = []
    print("[*] Starting NEA scraping run...")
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for index, c_info in enumerate(NEA_CEREMONIES):
            futures.append(executor.submit(scrape_ceremony_worker, c_info, index))
            
        for future in as_completed(futures):
            combined_results.extend(future.result())
            
    df = pd.DataFrame(combined_results)
    if not df.empty:
        df = df.sort_values(by=["year", "category", "winner", "nominee"], ascending=[True, True, False, True])
        df = df.drop_duplicates(subset=["year", "category", "nominee", "film"])
        
        import csv
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_file_path = os.path.join(output_dir, "nea_awards.csv")
        df.to_csv(output_file_path, index=False, quoting=csv.QUOTE_MINIMAL)
        print(f"[+] NEA data saved to: {output_file_path}")
        print(f"Total Unique Nominations: {len(df)}")
    else:
        print("[-] ERROR: No NEA records scraped.")

if __name__ == "__main__":
    main()
