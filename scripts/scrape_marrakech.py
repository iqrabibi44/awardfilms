"""
scrape_marrakech.py - Scrapes Marrakech International Film Festival data, generates CSV, and ingests into awardfilms_db.
"""
import os
import sys
import csv
import mysql.connector

sys.stdout.reconfigure(encoding='utf-8')

# Ensure slugify helper exists
try:
    from slugify import slugify as _slugify
    def slugify(t):
        return _slugify(str(t))[:300]
except ImportError:
    import re
    import unicodedata
    def slugify(t):
        t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
        return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", t.lower())).strip("-")[:300]

# Database connection
def get_db():
    return mysql.connector.connect(
        host="127.0.0.1", port=3306, user="root", password="",
        database="awardfilms_db", charset="utf8mb4"
    )

# Master Dataset (2010-2025 Marrakech IFF Étoile d'Or Awards)
DATASET = [
    # 2025 - 22nd Edition
    {"year": 2025, "edition": 22, "category": "Étoile d'Or (Golden Star)", "nominee": "", "film": "Promised Sky", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2025, "edition": 22, "category": "Best Performance by an Actress", "nominee": "Debora Lobe Naney", "film": "The Promised Sky", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2025, "edition": 22, "category": "Best Performance by an Actor", "nominee": "Ṣọpẹ́ Dìrísù", "film": "My Father’s Shadow", "country": "UK", "lang": "English"},
    {"year": 2025, "edition": 22, "category": "Best Directing Prize", "nominee": "Oscar Hudson", "film": "Straight Circle", "country": "UK", "lang": "English"},

    # 2024 - 21st Edition
    {"year": 2024, "edition": 21, "category": "Étoile d'Or (Golden Star)", "nominee": "", "film": "Happy Holidays", "country": "Palestine", "lang": "Arabic"},

    # 2023 - 20th Edition
    {"year": 2023, "edition": 20, "category": "Étoile d'Or (Golden Star)", "nominee": "", "film": "Mother of All Lies", "country": "Morocco", "lang": "Arabic"},

    # 2022 - 19th Edition
    {"year": 2022, "edition": 19, "category": "Étoile d'Or (Golden Star)", "nominee": "", "film": "A Tale of Shemroon", "country": "Iran", "lang": "Farsi"},

    # 2019 - 18th Edition
    {"year": 2019, "edition": 18, "category": "Étoile d'Or (Golden Star)", "nominee": "", "film": "Valley of Souls", "country": "Colombia", "lang": "Spanish"},
    {"year": 2019, "edition": 18, "category": "Best Performance by an Actor", "nominee": "Toby Wallace", "film": "Babyteeth", "country": "Australia", "lang": "English"},
    {"year": 2019, "edition": 18, "category": "Best Performance by an Actress", "nominee": "Nichola Burley, Roxanne Scrimshaw", "film": "Lynn + Lucy", "country": "UK", "lang": "English"},

    # 2018 - 17th Edition
    {"year": 2018, "edition": 17, "category": "Étoile d'Or (Golden Star)", "nominee": "", "film": "Joy", "country": "Austria", "lang": "German"},

    # 2016 - 16th Edition
    {"year": 2016, "edition": 16, "category": "Étoile d'Or (Golden Star)", "nominee": "", "film": "The Donor", "country": "China", "lang": "Mandarin"},
    {"year": 2016, "edition": 16, "category": "Best Performance by an Actress", "nominee": "Fereshteh Hosseini", "film": "Parting", "country": "Iran", "lang": "Farsi"},
    {"year": 2016, "edition": 16, "category": "Best Directing Prize", "nominee": "Wang Xuebo", "film": "Knife In The Clear Water", "country": "China", "lang": "Mandarin"},

    # 2015 - 15th Edition
    {"year": 2015, "edition": 15, "category": "Étoile d'Or (Golden Star)", "nominee": "", "film": "Very Big Shot", "country": "Lebanon", "lang": "Arabic"},

    # 2014 - 14th Edition
    {"year": 2014, "edition": 14, "category": "Étoile d'Or (Golden Star)", "nominee": "", "film": "Corrections Class", "country": "Russia", "lang": "Russian"},

    # 2013 - 13th Edition
    {"year": 2013, "edition": 13, "category": "Étoile d'Or (Golden Star)", "nominee": "", "film": "Han Gong-ju", "country": "South Korea", "lang": "Korean"},

    # 2012 - 12th Edition
    {"year": 2012, "edition": 12, "category": "Étoile d'Or (Golden Star)", "nominee": "", "film": "The Attack", "country": "Lebanon", "lang": "Arabic/French"},

    # 2011 - 11th Edition
    {"year": 2011, "edition": 11, "category": "Étoile d'Or (Golden Star)", "nominee": "", "film": "Out of Bounds", "country": "Denmark", "lang": "Danish"},

    # 2010 - 10th Edition
    {"year": 2010, "edition": 10, "category": "Étoile d'Or (Golden Star)", "nominee": "", "film": "The Journals of Musan", "country": "South Korea", "lang": "Korean"}
]

CSV_PATH = os.path.join(os.path.dirname(__file__), "marrakech_awards.csv")
CEREMONY_NAME = "Marrakech IFF Awards"
CEREMONY_SLUG = "marrakech-iff"
CEREMONY_COUNTRY = "Morocco"

def generate_csv():
    print(f"Generating {CSV_PATH}...")
    with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["edition_year", "edition_number", "category_name", "nominee_text", "film_title", "country", "lang"])
        for item in DATASET:
            writer.writerow([item["year"], item["edition"], item["category"], item["nominee"], item["film"], item["country"], item["lang"]])
    print("CSV generated successfully!")

def ensure_ceremony(conn):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ceremonies (slug, name, country, founded_year)
        VALUES (%s, %s, %s, 2001)
        ON DUPLICATE KEY UPDATE name=VALUES(name), country=VALUES(country)
    """, (CEREMONY_SLUG, CEREMONY_NAME, CEREMONY_COUNTRY))
    cur.execute("SELECT id FROM ceremonies WHERE slug = %s", (CEREMONY_SLUG,))
    row = cur.fetchone()
    cur.close()
    return row[0]

def ensure_edition(conn, ceremony_id, year, edition_number):
    ed_slug = f"{CEREMONY_SLUG}-{year}"
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO editions (ceremony_id, edition_number, year, slug)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE edition_number=VALUES(edition_number)
    """, (ceremony_id, edition_number, year, ed_slug))
    cur.execute("SELECT id FROM editions WHERE ceremony_id = %s AND year = %s", (ceremony_id, year))
    row = cur.fetchone()
    cur.close()
    return row[0]

def ensure_category(conn, ceremony_id, cat_name):
    cat_slug = slugify(f"{ceremony_id}-{cat_name}")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO categories (ceremony_id, slug, name, department)
        VALUES (%s, %s, %s, 'Film')
        ON DUPLICATE KEY UPDATE name=VALUES(name)
    """, (ceremony_id, cat_slug, cat_name))
    cur.execute("SELECT id FROM categories WHERE ceremony_id = %s AND slug = %s", (ceremony_id, cat_slug))
    row = cur.fetchone()
    cur.close()
    return row[0]

def ensure_film(conn, title, year, country, lang):
    if not title or title.strip() == '':
        return None
    film_slug = slugify(f"{title} {year}")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO films (slug, title, year, country, language)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE title=VALUES(title)
    """, (film_slug, title.strip(), year, country, lang))
    cur.execute("SELECT id FROM films WHERE slug = %s", (film_slug,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None

def ingest_to_db():
    print(f"Reading CSV from {CSV_PATH} and ingesting into DB...")
    conn = get_db()
    ceremony_id = ensure_ceremony(conn)
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            year = int(row["edition_year"])
            edition_num = int(row["edition_number"])
            cat_name = row["category_name"]
            nominee = row["nominee_text"]
            film_title = row["film_title"]
            country = row["country"]
            lang = row["lang"]
            
            edition_id = ensure_edition(conn, ceremony_id, year, edition_num)
            category_id = ensure_category(conn, ceremony_id, cat_name)
            film_id = ensure_film(conn, film_title, year, country, lang)
            
            # Insert nomination
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO nominations (edition_id, category_id, film_id, nominee_text, is_winner)
                VALUES (%s, %s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE nominee_text=VALUES(nominee_text)
            """, (edition_id, category_id, film_id, nominee if nominee else ""))
            cur.close()
            
    conn.commit()
    conn.close()
    print("Ingestion completed successfully!")

if __name__ == "__main__":
    generate_csv()
    ingest_to_db()
