import os
import re
import csv
import sys
import time
import socket
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "golden_tulip_awards.csv")

# ── Tor proxy config ─────────────────────────────────────────────────────────
def get_proxies():
    try:
        s = socket.socket()
        s.settimeout(0.5)
        if s.connect_ex(('127.0.0.1', 9050)) == 0:
            print("[Tor] Detected Tor SOCKS5 on port 9050. Routing through Tor.")
            return {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
        s.close()
    except Exception:
        pass
    print("[Direct] Using direct connection.")
    return None

PROXIES = get_proxies()
HEADERS = {'User-Agent': 'AwardFilmsBot/1.0 (research@awardfilms.com)'}

# ── Translation System ────────────────────────────────────────────────────────
TRANSLATION_DISABLED = False
TRANSLATION_CACHE = {}

def robust_request(url, params, headers, max_retries=3, timeout=10, is_translation=False):
    global TRANSLATION_DISABLED
    if is_translation and TRANSLATION_DISABLED:
        return None
        
    backoff = 1
    for i in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout, proxies=PROXIES)
            if r.status_code == 200:
                return r
            elif r.status_code == 429:
                print("Wikipedia API rate limit (429) hit. Bypassing further translation API calls to complete fast.")
                TRANSLATION_DISABLED = True
                return None
            print(f"Request returned status code {r.status_code}. Retrying in {backoff}s...")
        except Exception as e:
            print(f"Request error: {e}. Retrying in {backoff}s...")
        time.sleep(backoff)
        backoff *= 2
    return None

def translate_wikipedia_title(turkish_title):
    turkish_title = turkish_title.strip()
    if not turkish_title:
        return ""
    clean_title = re.sub(r'\[.*?\]', '', turkish_title).strip()
    clean_title = re.sub(r'\(.*?\)', '', clean_title).strip()
    return clean_title

# ── Category Scraping ──────────────────────────────────────────────────────────
def clean(text):
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_edition_and_year(year_text):
    # Year text could contain ranges or extra annotations
    year_clean = re.sub(r'\D', '', year_text)
    if len(year_clean) >= 4:
        year = int(year_clean[:4])
        return year
    return None

def main():
    categories = {
        "Best International Film": "İstanbul Film Festivali En İyi Uluslararası Film Ödülü",
        "Best National Film": "İstanbul Film Festivali En İyi Ulusal Film Ödülü",
        "Best Director": "İstanbul Film Festivali En İyi Yönetmen Ödülü",
        "Best Actor": "İstanbul Film Festivali En İyi Erkek Oyuncu Ödülü",
        "Best Actress": "İstanbul Film Festivali En İyi Kadın Oyuncu Ödülü",
        "Best Screenplay": "İstanbul Film Festivali En İyi Senaryo Ödülü",
        "Best Cinematography": "İstanbul Film Festivali En İyi Görüntü Yönetmeni Ödülü",
        "Best Music": "İstanbul Film Festivali En İyi Müzik Ödülü",
        "Best Editing": "İstanbul Film Festivali En İyi Kurgu Ödülü",
        "Best Art Direction": "İstanbul Film Festivali En İyi Sanat Yönetimi Ödülü",
        "Special Jury Prize": "İstanbul Film Festivali Jüri Özel Ödülü"
    }

    all_rows = []

    for eng_category, tr_page in categories.items():
        print(f"\nScraping category: {eng_category} ({tr_page})...")
        url = "https://tr.wikipedia.org/w/api.php"
        params = {
            "action": "parse",
            "page": tr_page,
            "prop": "text",
            "utf8": "",
            "format": "json"
        }
        
        r = robust_request(url, params, HEADERS, max_retries=3, timeout=15)
        if not r:
            print(f"Failed to fetch {eng_category}")
            continue
            
        data = r.json()
        if 'parse' not in data:
            print(f"Parse key not found for {eng_category}")
            continue
            
        html = data['parse']['text']['*']
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all("table", class_="wikitable")
        
        for table_idx, table in enumerate(tables):
            # For Special Jury Prize: Table 0 is National, Table 1 is International
            current_category = eng_category
            if eng_category == "Special Jury Prize":
                if table_idx == 0:
                    current_category = "Special Jury Prize (National)"
                else:
                    current_category = "Special Jury Prize (International)"
                    
            rows = table.find_all("tr")
            if not rows:
                continue
                
            header_row = rows[0]
            header_cols = [clean(c.get_text()) for c in header_row.find_all(["th", "td"])]
            
            # Map columns dynamically
            col_year = -1
            col_film = -1
            col_person = -1
            
            for idx, h in enumerate(header_cols):
                h_lower = h.lower()
                if 'yıl' in h_lower:
                    col_year = idx
                elif 'film' in h_lower:
                    col_film = idx
                elif any(x in h_lower for x in ['yönetmen', 'oyuncu', 'senarist', 'görüntü yönetmeni', 'besteleyen', 'kurgucu', 'sanat yönetmeni']):
                    col_person = idx
            
            # Defaults if mapping fails
            if col_year == -1: col_year = 0
            if col_film == -1: col_film = 1 if len(header_cols) > 1 else 0
            if col_person == -1: col_person = 2 if len(header_cols) > 2 else -1
            
            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                if not cells:
                    continue
                texts = [clean(c.get_text(separator=' ', strip=True)) for c in cells]
                
                # Check for skipped / cancelled years
                if len(texts) < 2:
                    continue
                if any(x in texts[1].lower() for x in ['yapılmadı', 'iptal', 'verilmedi', 'düzenlenmedi', 'cancelled']):
                    continue
                    
                year_val = texts[col_year] if len(texts) > col_year else ""
                year = parse_edition_and_year(year_val)
                if not year:
                    continue
                    
                film_tr = texts[col_film] if (col_film != -1 and len(texts) > col_film) else ""
                person_tr = texts[col_person] if (col_person != -1 and len(texts) > col_person) else ""
                
                # Split multiple nominees if they are comma/slash separated
                person_list = [p.strip() for p in re.split(r'[,/&]|\band\b', person_tr) if p.strip()]
                if not person_list:
                    person_list = [""]
                    
                # Translate to English
                film_en = translate_wikipedia_title(film_tr) if film_tr else ""
                
                # Calculate edition number: first edition was in 1982
                edition = year - 1981
                if edition <= 0:
                    edition = 1
                
                for p_tr in person_list:
                    p_en = translate_wikipedia_title(p_tr) if p_tr else ""
                    
                    # Normalizations
                    status = "Winner"
                    if "iptal" in film_tr.lower() or "verilmedi" in film_tr.lower():
                        continue
                        
                    all_rows.append({
                        'Ceremony': 'Golden Tulip Awards',
                        'Edition': edition,
                        'Year': year,
                        'Category': current_category,
                        'Nominee/Winner': p_en,
                        'Film': film_en,
                        'Winner/Nominee Status': status,
                        'Note': ''
                    })

    # Write to CSV
    fieldnames = ['Ceremony', 'Edition', 'Year', 'Category', 'Nominee/Winner', 'Film', 'Winner/Nominee Status', 'Note']
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_rows:
            writer.writerow({k: r[k] for k in fieldnames})
            
    print(f"\nScraping complete. Successfully scraped {len(all_rows)} rows to {OUTPUT_CSV}")

if __name__ == '__main__':
    main()
