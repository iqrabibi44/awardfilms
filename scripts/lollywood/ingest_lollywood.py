import os
import sys
import pandas as pd
import mysql.connector

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
try:
    from slugify import slugify as _slugify
    def slugify(t):
        return _slugify(str(t))[:300]
except ImportError:
    import unicodedata
    import re
    def slugify(t):
        t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
        return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", t.lower())).strip("-")[:300]

def get_db():
    return mysql.connector.connect(host="127.0.0.1", port=3306, user="root", password="", database="awardfilms_db", charset="utf8mb4")

def ingest_lollywood():
    conn = get_db()
    cur = conn.cursor()
    
    csv_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "lib", "data", "lollywood")
    if not os.path.exists(csv_dir):
        print(f"Directory {csv_dir} does not exist.")
        return
        
    csvs = [os.path.join(csv_dir, f) for f in os.listdir(csv_dir) if f.endswith(".csv")]
    
    inserted = 0
    for csv_file in csvs:
        print(f"Processing {csv_file}")
        df = pd.read_csv(csv_file)
        
        for _, row in df.iterrows():
            award_show = str(row['award_show']).strip()
            category = str(row['category']).strip()
            
            try:
                year = int(str(row['year']).strip()[:4])
            except:
                continue
            
            winner = str(row.get('winner', '')).strip()
            film = str(row.get('film', '')).strip()
            
            if winner in ['nan', 'None', '']:
                winner = film
            if film in ['nan', 'None', '']:
                film = winner
                
            if film in ['nan', 'None', '']:
                continue
                
            c_slug = slugify(award_show)[:200]
            cur.execute("INSERT IGNORE INTO ceremonies (slug, name, country) VALUES (%s, %s, 'Pakistan')", (c_slug, award_show))
            cur.execute("SELECT id FROM ceremonies WHERE slug = %s", (c_slug,))
            res = cur.fetchone()
            if not res: continue
            c_id = res[0]
            
            ed_slug = f"{c_slug}-{year}"[:200]
            cur.execute("INSERT IGNORE INTO editions (ceremony_id, year, slug) VALUES (%s, %s, %s)", (c_id, year, ed_slug))
            cur.execute("SELECT id FROM editions WHERE ceremony_id = %s AND year = %s", (c_id, year))
            res = cur.fetchone()
            if not res: continue
            e_id = res[0]
            
            cat_slug = slugify(f"{c_id}-{category}")[:200]
            cur.execute("INSERT IGNORE INTO categories (ceremony_id, slug, name, department) VALUES (%s, %s, %s, 'General')", (c_id, cat_slug, category))
            cur.execute("SELECT id FROM categories WHERE ceremony_id = %s AND slug = %s", (c_id, cat_slug))
            res = cur.fetchone()
            if not res: continue
            cat_id = res[0]
            
            f_slug = slugify(f"{film} {year-1}")[:200]
            cur.execute("INSERT IGNORE INTO films (slug, title, year, country, language) VALUES (%s, %s, %s, 'Pakistan', 'Urdu')", (f_slug, film, year-1))
            cur.execute("SELECT id FROM films WHERE slug = %s", (f_slug,))
            res = cur.fetchone()
            if not res: continue
            f_id = res[0]
            
            cur.execute("INSERT IGNORE INTO nominations (edition_id, category_id, film_id, is_winner, nominee_text) VALUES (%s, %s, %s, 1, %s)", (e_id, cat_id, f_id, winner))
            inserted += 1
            
    conn.commit()
    cur.close()
    print(f"Total Lollywood nominations inserted: {inserted}")

if __name__ == "__main__":
    ingest_lollywood()
