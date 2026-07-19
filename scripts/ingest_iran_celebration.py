import os
import sys
import re
import csv
import mysql.connector

sys.stdout.reconfigure(encoding='utf-8')

# Import slugify helper
try:
    from slugify import slugify as _slugify
    def slugify(t):
        return _slugify(str(t))[:300]
except ImportError:
    import unicodedata
    def slugify(t):
        t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
        return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", t.lower())).strip("-")[:300]

# Add project root to sys.path so we can import lib.text_spinner
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from lib.text_spinner import TextParaphraser
    paraphraser = TextParaphraser()
except Exception:
    paraphraser = None

def get_db():
    return mysql.connector.connect(
        host="127.0.0.1", port=3306, user="root", password="",
        database="awardfilms_db", charset="utf8mb4"
    )

def ensure_ceremony(conn, name):
    # Use fixed slug that matches navigation.php exactly
    SLUG_MAP = {
        "Iran Cinema Celebration Awards": "iran-cinema-celebration",
    }
    slug = SLUG_MAP.get(name, slugify(name))
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ceremonies (slug, name, country)
        VALUES (%s, %s, 'Iran')
        ON DUPLICATE KEY UPDATE name=VALUES(name), country=VALUES(country)
        """, (slug, name)
    )
    cur.execute("SELECT id FROM ceremonies WHERE slug = %s", (slug,))
    row = cur.fetchone()
    cur.close()
    return row[0]

def ensure_edition(conn, ceremony_id, year, edition_number, prefix):
    ed_slug = f"{prefix}-{year}"
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO editions (ceremony_id, edition_number, year, slug)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE slug = VALUES(slug), edition_number = VALUES(edition_number)
        """, (ceremony_id, edition_number, year, ed_slug)
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

def ensure_film(conn, title, year):
    film_slug = slugify(f"{title} {year}")
    if not film_slug:
        return None
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO films (slug, title, year, country, language)
        VALUES (%s, %s, %s, 'Iran', 'Persian')
        ON DUPLICATE KEY UPDATE title=VALUES(title)
        """, (film_slug, title, year)
    )
    cur.execute("SELECT id FROM films WHERE slug = %s", (film_slug,))
    row = cur.fetchone()
    cur.close()
    return row[0]

def main():
    csv_path = r"c:\Users\INFOTECH\OneDrive\Desktop\Awardfilms\scripts\iran_cinema_celebration.csv"
    if not os.path.exists(csv_path):
        print(f"Error: Scraped CSV not found at {csv_path}")
        return

    conn = get_db()
    cur = conn.cursor()
    
    # Read CSV rows
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    print(f"Ingesting {len(rows)} records into awardfilms_db...")
    
    ceremonies = {}
    editions = {}
    categories = {}
    films = {}
    inserted_count = 0
    
    for row in rows:
        ceremony_name = row['Ceremony']
        edition_str = row['Edition']
        year = int(row['Year'])
        category_name = row['Category']
        nominee_text = row['Nominee/Winner']
        film_title = row['Film']
        
        # 1. Ceremony
        if ceremony_name not in ceremonies:
            ceremonies[ceremony_name] = ensure_ceremony(conn, ceremony_name)
        c_id = ceremonies[ceremony_name]
        
        # 2. Edition
        ed_num = int(re.sub(r'\D', '', edition_str))
        ed_key = f"{c_id}-{year}"
        if ed_key not in editions:
            editions[ed_key] = ensure_edition(conn, c_id, year, ed_num, slugify(ceremony_name))
        e_id = editions[ed_key]
        
        # 3. Category
        cat_key = f"{c_id}-{category_name}"
        if cat_key not in categories:
            categories[cat_key] = ensure_category(conn, c_id, category_name)
        cat_id = categories[cat_key]
        
        # 4. Film (release year is ceremony year - 1)
        film_title = film_title.strip() if film_title else nominee_text.strip()
        film_key = f"{film_title}-{year - 1}"
        if film_key not in films:
            films[film_key] = ensure_film(conn, film_title, year - 1)
        f_id = films[film_key]
        
        if not f_id:
            continue
            
        # 5. Nominee Text
        spun_text = nominee_text.strip()
        if paraphraser:
            try:
                spun_text = paraphraser.paraphrase(spun_text)
            except Exception:
                pass
                
        # 6. Ingest Nomination
        cur.execute(
            """
            INSERT IGNORE INTO nominations
                (edition_id, category_id, film_id, nominee_text, is_winner, source_ref)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (e_id, cat_id, f_id, spun_text, 1, 'Wikipedia')
        )
        inserted_count += cur.rowcount

    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Successfully ingested {inserted_count} nominations into the database.")

if __name__ == '__main__':
    main()
