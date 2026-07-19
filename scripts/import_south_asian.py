import os
import sys
import pandas as pd
import mysql.connector
from tqdm import tqdm
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from lib.text_spinner import TextParaphraser

try:
    from slugify import slugify as _slugify
    def slugify(t):
        return _slugify(str(t))[:190]
except ImportError:
    import unicodedata
    def slugify(t):
        t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
        return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", t.lower())).strip("-")[:190]

def get_db():
    return mysql.connector.connect(
        host="127.0.0.1", port=3306, user="root", password="",
        database="awardfilms_db", charset="utf8mb4"
    )

def ensure_ceremony(conn, name, country):
    slug = slugify(name)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ceremonies (slug, name, country)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE name=VALUES(name)
        """, (slug, name, country)
    )
    cur.execute("SELECT id FROM ceremonies WHERE slug = %s", (slug,))
    row = cur.fetchone()
    cur.close()
    return row[0]

def ensure_edition(conn, ceremony_id, year, prefix):
    ed_slug = f"{prefix}-{year}"
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO editions (ceremony_id, year, slug)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE slug = VALUES(slug)
        """, (ceremony_id, year, ed_slug)
    )
    cur.execute("SELECT id FROM editions WHERE ceremony_id = %s AND year = %s", (ceremony_id, year))
    row = cur.fetchone()
    cur.close()
    return row[0]

def ensure_category(conn, ceremony_id, cat_name):
    cat_slug = slugify(f"{ceremony_id}-{cat_name}")
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO categories (ceremony_id, slug, name, department)
        VALUES (%s, %s, %s, 'General')
        ON DUPLICATE KEY UPDATE name = VALUES(name)
        """, (ceremony_id, cat_slug, cat_name)
    )
    cur.execute("SELECT id FROM categories WHERE ceremony_id = %s AND slug = %s", (ceremony_id, cat_slug))
    row = cur.fetchone()
    cur.close()
    return row[0]

def ensure_film(conn, title, year, country, language):
    film_slug = slugify(f"{title} {year}")
    if not film_slug:
        return None
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO films (slug, title, year, country, language)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE title=VALUES(title)
        """, (film_slug, title, year, country, language)
    )
    cur.execute("SELECT id FROM films WHERE slug = %s", (film_slug,))
    row = cur.fetchone()
    cur.close()
    return row[0]

def process_south_asian_master(conn, csv_path, default_country, paraphraser):
    if not os.path.exists(csv_path):
        print(f"Skipping (not found): {csv_path}")
        return
        
    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    # clean missing years or award shows
    df = df.dropna(subset=['award_show', 'year'])
    
    # caches
    ceremonies = {}
    editions = {}
    categories = {}
    films = {}
    
    inserted = 0
    cur = conn.cursor()
    for _, row in tqdm(df.iterrows(), total=len(df), desc=os.path.basename(csv_path)):
        award_show = str(row['award_show']).strip()
        try:
            year = int(str(row['year'])[:4])
        except:
            continue
            
        category_name = str(row['category']).strip()
        if category_name.startswith("Unspecified"):
            category_name = "Best Film/Actor/General"
            
        film_title = str(row['work_title']).strip()
        nominee_name = str(row['nominee_name']).strip()
        
        if pd.isna(row['work_title']) or film_title == 'nan':
            film_title = nominee_name
        if pd.isna(row['nominee_name']) or nominee_name == 'nan':
            nominee_name = film_title
            
        if pd.isna(film_title) or film_title == 'nan':
            continue
            
        is_winner = 1 if str(row.get('result', '')).lower() == 'winner' else 0
        language = str(row.get('language', 'Unknown'))
        
        # 1. Ceremony
        if award_show not in ceremonies:
            ceremonies[award_show] = ensure_ceremony(conn, award_show, default_country)
        c_id = ceremonies[award_show]
        
        # 2. Edition
        ed_key = f"{c_id}-{year}"
        if ed_key not in editions:
            editions[ed_key] = ensure_edition(conn, c_id, year, slugify(award_show))
        e_id = editions[ed_key]
        
        # 3. Category
        cat_key = f"{c_id}-{category_name}"
        if cat_key not in categories:
            categories[cat_key] = ensure_category(conn, c_id, category_name)
        cat_id = categories[cat_key]
        
        # 4. Film
        film_key = f"{film_title}-{year}"
        if film_key not in films:
            films[film_key] = ensure_film(conn, film_title, year - 1, default_country, language)
        f_id = films[film_key]
        
        if not f_id:
            continue
            
        # 5. Paraphrase nominee text
        spun_text = nominee_name
        
        source = str(row.get('source_url', ''))
        
        cur.execute(
            """
            INSERT IGNORE INTO nominations
                (edition_id, category_id, film_id, nominee_text, is_winner, source_ref)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (e_id, cat_id, f_id, spun_text, is_winner, source)
        )
        inserted += 1
        
    conn.commit()
    cur.close()
    print(f" -> Inserted {inserted} nominations.\n")


def main():
    conn = get_db()
    paraphraser = TextParaphraser()
    
    # Process South Asian
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    process_south_asian_master(
        conn,
        os.path.join(base_dir, "scripts", "tollywood_scraper", "output", "tollywood_awards_master.csv"),
        "India",
        paraphraser
    )
    
    process_south_asian_master(
        conn,
        os.path.join(base_dir, "scripts", "mollywood_scraper", "output", "mollywood_awards_master.csv"),
        "India",
        paraphraser
    )
    
    process_south_asian_master(
        conn,
        os.path.join(base_dir, "scripts", "sandalwood_scraper", "output", "sandalwood_awards_master.csv"),
        "India",
        paraphraser
    )
    
    conn.close()
    print("Done importing South Asian masters!")

if __name__ == "__main__":
    main()
