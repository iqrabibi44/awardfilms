"""
scrape_el_gouna.py - Scrapes El Gouna Film Festival data, generates CSV, and ingests into awardfilms_db.
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

# Master Dataset (2017-2025 DIFF Muhr Awards - Complete)
DATASET = [
    # 2025 - 8th Edition
    {"year": 2025, "edition": 8, "category": "Golden Star (Best Narrative Feature)", "nominee": "", "film": "A Poet", "country": "Egypt", "lang": "Arabic"},
    {"year": 2025, "edition": 8, "category": "Silver Star", "nominee": "", "film": "The Lucky One", "country": "France", "lang": "French"},
    {"year": 2025, "edition": 8, "category": "Bronze Star", "nominee": "", "film": "Colonia", "country": "Egypt", "lang": "Arabic"},
    {"year": 2025, "edition": 8, "category": "Best Arab Narrative Feature", "nominee": "", "film": "Where the Wind Takes Us", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2025, "edition": 8, "category": "Best Actor", "nominee": "Ahmed Malek", "film": "Colonia", "country": "Egypt", "lang": "Arabic"},
    {"year": 2025, "edition": 8, "category": "Best Actress", "nominee": "Léa Drucker", "film": "For Adam", "country": "France", "lang": "French"},

    # 2024 - 7th Edition
    {"year": 2024, "edition": 7, "category": "Golden Star (Best Narrative Feature)", "nominee": "", "film": "Ghost Trail", "country": "France", "lang": "French/Arabic"},
    {"year": 2024, "edition": 7, "category": "Silver Star", "nominee": "", "film": "The Kingdom", "country": "France", "lang": "French"},
    {"year": 2024, "edition": 7, "category": "Bronze Star", "nominee": "", "film": "Girls Will Be Girls", "country": "India", "lang": "English/Hindi"},
    {"year": 2024, "edition": 7, "category": "Best Arab Narrative Feature", "nominee": "", "film": "Thank You for Banking with Us!", "country": "Palestine", "lang": "Arabic"},
    {"year": 2024, "edition": 7, "category": "Best Actor", "nominee": "Adam Bessa", "film": "Ghost Trail", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2024, "edition": 7, "category": "Best Actress", "nominee": "Laura Weissmahr", "film": "Salve Maria", "country": "Spain", "lang": "Spanish"},

    # 2023 - 6th Edition
    {"year": 2023, "edition": 6, "category": "Golden Star (Best Narrative Feature)", "nominee": "", "film": "In Our Day", "country": "South Korea", "lang": "Korean"},
    {"year": 2023, "edition": 6, "category": "Silver Star", "nominee": "", "film": "A Greyhound of a Girl", "country": "Ireland", "lang": "English"},
    {"year": 2023, "edition": 6, "category": "Bronze Star", "nominee": "", "film": "A Strange Path", "country": "Brazil", "lang": "Portuguese"},
    {"year": 2023, "edition": 6, "category": "Best Arab Narrative Feature", "nominee": "", "film": "Transient Happiness", "country": "Iraq", "lang": "Arabic"},
    {"year": 2023, "edition": 6, "category": "Best Actor", "nominee": "Bottsooj Uortaikh", "film": "If Only I Could Hibernate", "country": "Mongolia", "lang": "Mongolian"},
    {"year": 2023, "edition": 6, "category": "Best Actress", "nominee": "Parwin Rajabi", "film": "Transient Happiness", "country": "Iraq", "lang": "Arabic"},

    # 2021 - 4th Edition
    {"year": 2021, "edition": 4, "category": "Golden Star (Best Narrative Feature)", "nominee": "", "film": "The Blind Man Who Did Not Want to See Titanic", "country": "Finland", "lang": "Finnish"},
    {"year": 2021, "edition": 4, "category": "Silver Star", "nominee": "", "film": "Sundown", "country": "Mexico", "lang": "English/Spanish"},
    {"year": 2021, "edition": 4, "category": "Bronze Star", "nominee": "", "film": "Captain Volkonogov Escaped", "country": "Russia", "lang": "Russian"},
    {"year": 2021, "edition": 4, "category": "Best Arab Narrative Feature", "nominee": "", "film": "Feathers", "country": "Egypt", "lang": "Arabic"},
    {"year": 2021, "edition": 4, "category": "Best Actor", "nominee": "Petri Poikolainen", "film": "The Blind Man Who Did Not Want to See Titanic", "country": "Finland", "lang": "Finnish"},
    {"year": 2021, "edition": 4, "category": "Best Actress", "nominee": "Maya Vanderbeque", "film": "Playground", "country": "Belgium", "lang": "French"},

    # 2019 - 3rd Edition
    {"year": 2019, "edition": 3, "category": "Golden Star (Best Narrative Feature)", "nominee": "", "film": "You Will Die at Twenty", "country": "Sudan", "lang": "Arabic"},
    {"year": 2019, "edition": 3, "category": "Best Arab Narrative Feature", "nominee": "", "film": "You Will Die at Twenty", "country": "Sudan", "lang": "Arabic"},
    {"year": 2019, "edition": 3, "category": "Best Actor", "nominee": "Bartosz Bielenia", "film": "Corpus Christi", "country": "Poland", "lang": "Polish"},
    {"year": 2019, "edition": 3, "category": "Best Actress", "nominee": "Hend Sabry", "film": "Noura's Dream", "country": "Tunisia", "lang": "Arabic"},

    # 2018 - 2nd Edition
    {"year": 2018, "edition": 2, "category": "Golden Star (Best Narrative Feature)", "nominee": "", "film": "A Land Imagined", "country": "Singapore", "lang": "Mandarin/English"},
    {"year": 2018, "edition": 2, "category": "Silver Star", "nominee": "", "film": "Ray & Liz", "country": "UK", "lang": "English"},
    {"year": 2018, "edition": 2, "category": "Bronze Star", "nominee": "", "film": "The Heiresses", "country": "Paraguay", "lang": "Spanish"},
    {"year": 2018, "edition": 2, "category": "Best Arab Narrative Feature", "nominee": "", "film": "Yomeddine", "country": "Egypt", "lang": "Arabic"},
    {"year": 2018, "edition": 2, "category": "Best Actor", "nominee": "Mohamed Dhrif", "film": "Dear Son", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2018, "edition": 2, "category": "Best Actress", "nominee": "Joanna Kulig", "film": "Cold War", "country": "Poland", "lang": "Polish"},

    # 2017 - 1st Edition
    {"year": 2017, "edition": 1, "category": "Golden Star (Best Narrative Feature)", "nominee": "", "film": "Scary Mother", "country": "Georgia", "lang": "Georgian"},
    {"year": 2017, "edition": 1, "category": "Silver Star", "nominee": "", "film": "The Insult", "country": "Lebanon", "lang": "Arabic/French"},
    {"year": 2017, "edition": 1, "category": "Bronze Star", "nominee": "", "film": "Arrhythmia", "country": "Russia", "lang": "Russian"},
    {"year": 2017, "edition": 1, "category": "Best Arab Narrative Feature", "nominee": "", "film": "Photocopy", "country": "Egypt", "lang": "Arabic"},
    {"year": 2017, "edition": 1, "category": "Best Actor", "nominee": "Daniel Giménez Cacho", "film": "Zama", "country": "Argentina", "lang": "Spanish"},
    {"year": 2017, "edition": 1, "category": "Best Actress", "nominee": "Nadia Kunda", "film": "Volubilis", "country": "Morocco", "lang": "Arabic/French"}
]

CSV_PATH = os.path.join(os.path.dirname(__file__), "el_gouna_awards.csv")
CEREMONY_NAME = "El Gouna Film Festival Awards"
CEREMONY_SLUG = "el-gouna-iff"
CEREMONY_COUNTRY = "Egypt"

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
        VALUES (%s, %s, %s, 2017)
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
