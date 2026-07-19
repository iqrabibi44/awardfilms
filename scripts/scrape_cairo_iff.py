"""
scrape_cairo_iff.py - Scrapes Cairo International Film Festival data, generates CSV, and ingests into awardfilms_db.
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

# Master Dataset (2010-2025 editions)
DATASET = [
    # 2025 - 46th Edition
    {"year": 2025, "edition": 46, "category": "Golden Pyramid (Best Film)", "nominee": "", "film": "Dragonfly", "country": "UK", "lang": "English"},
    {"year": 2025, "edition": 46, "category": "Bronze Pyramid (Special Jury Award)", "nominee": "Seamus Alton", "film": "As We Breathe", "country": "USA", "lang": "English"},
    {"year": 2025, "edition": 46, "category": "Best Actor", "nominee": "Majd Eid", "film": "Once Upon a Time in Gaza", "country": "Palestine", "lang": "Arabic"},
    {"year": 2025, "edition": 46, "category": "Best Actress", "nominee": "Andrea Riseborough", "film": "Dragonfly", "country": "UK", "lang": "English"},

    # 2024 - 45th Edition
    {"year": 2024, "edition": 45, "category": "Golden Pyramid (Best Film)", "nominee": "", "film": "The New Year That Never Came", "country": "Romania", "lang": "Romanian"},
    {"year": 2024, "edition": 45, "category": "Silver Pyramid (Special Jury Award)", "nominee": "Natalia Nazarova", "film": "Postmarks", "country": "Russia", "lang": "Russian"},
    {"year": 2024, "edition": 45, "category": "Bronze Pyramid (Best First/Second Work)", "nominee": "Pedro Freire", "film": "Malu", "country": "Brazil", "lang": "Portuguese"},
    {"year": 2024, "edition": 45, "category": "Best Actor", "nominee": "Lee Kang Sheng", "film": "Blue Sun Palace", "country": "Taiwan", "lang": "Mandarin"},
    {"year": 2024, "edition": 45, "category": "Best Actress", "nominee": "Yara de Novaes", "film": "Malu", "country": "Brazil", "lang": "Portuguese"},

    # 2022 - 44th Edition
    {"year": 2022, "edition": 44, "category": "Golden Pyramid (Best Film)", "nominee": "", "film": "Alam", "country": "Palestine", "lang": "Arabic"},
    {"year": 2022, "edition": 44, "category": "Silver Pyramid (Special Jury Award)", "nominee": "Gregorio Graziosi", "film": "Tinnitus", "country": "Brazil", "lang": "Portuguese"},
    {"year": 2022, "edition": 44, "category": "Best Actor", "nominee": "Maher Al Khair", "film": "The Dam", "country": "Sudan", "lang": "Arabic"},
    {"year": 2022, "edition": 44, "category": "Best Actress", "nominee": "Maisa Abd Elhadi", "film": "Huda’s Salon", "country": "Palestine", "lang": "Arabic"},

    # 2021 - 43rd Edition
    {"year": 2021, "edition": 43, "category": "Golden Pyramid (Best Film)", "nominee": "", "film": "The Hole in the Fence", "country": "Mexico", "lang": "Spanish"},
    {"year": 2021, "edition": 43, "category": "Silver Pyramid (Special Jury Award)", "nominee": "Mariano Cohn, Gastón Duprat", "film": "Official Competition", "country": "Spain", "lang": "Spanish"},
    {"year": 2021, "edition": 43, "category": "Best Actor", "nominee": "Mohamed Mellali", "film": "The Odd-Job Men", "country": "Spain", "lang": "Spanish"},
    {"year": 2021, "edition": 43, "category": "Best Actress", "nominee": "Swamy Rotolo", "film": "A Chiara", "country": "Italy", "lang": "Italian"},

    # 2020 - 42nd Edition
    {"year": 2020, "edition": 42, "category": "Golden Pyramid (Best Film)", "nominee": "", "film": "Limbo", "country": "UK", "lang": "English"},
    {"year": 2020, "edition": 42, "category": "Silver Pyramid (Special Jury Award)", "nominee": "Arab Nasser, Tarzan Nasser", "film": "Gaza Mon Amour", "country": "Palestine", "lang": "Arabic"},
    {"year": 2020, "edition": 42, "category": "Best Actor", "nominee": "Sami Bouajila", "film": "A Son", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2020, "edition": 42, "category": "Best Actress", "nominee": "Ilse Fritch", "film": "Naft", "country": "Mexico", "lang": "Spanish"},

    # 2019 - 41st Edition
    {"year": 2019, "edition": 41, "category": "Golden Pyramid (Best Film)", "nominee": "", "film": "I'm No Longer Here", "country": "Mexico", "lang": "Spanish"},
    {"year": 2019, "edition": 41, "category": "Silver Pyramid (Special Jury Award)", "nominee": "Denis Côté", "film": "Ghost Town Anthology", "country": "Canada", "lang": "French"},
    {"year": 2019, "edition": 41, "category": "Best Actor", "nominee": "Juan Daniel Garcia", "film": "I'm No Longer Here", "country": "Mexico", "lang": "Spanish"},
    {"year": 2019, "edition": 41, "category": "Best Actress", "nominee": "Judy Ann Santos", "film": "Mindanao", "country": "Philippines", "lang": "Tagalog"},

    # 2018 - 40th Edition
    {"year": 2018, "edition": 40, "category": "Golden Pyramid (Best Film)", "nominee": "", "film": "A Twelve-Year Night", "country": "Uruguay", "lang": "Spanish"},
    {"year": 2018, "edition": 40, "category": "Silver Pyramid (Special Jury Award)", "nominee": "Phuttiphong Aroonpheng", "film": "Manta Ray", "country": "Thailand", "lang": "Thai"},
    {"year": 2018, "edition": 40, "category": "Best Actor", "nominee": "Sherif Desoky", "film": "Night/Exterior", "country": "Egypt", "lang": "Arabic"},
    {"year": 2018, "edition": 40, "category": "Best Actress", "nominee": "Luisa Harland", "film": "Sunday's Illness", "country": "Spain", "lang": "Spanish"},

    # 2017 - 39th Edition
    {"year": 2017, "edition": 39, "category": "Golden Pyramid (Best Film)", "nominee": "", "film": "The Intruder", "country": "Italy", "lang": "Italian"},
    {"year": 2017, "edition": 39, "category": "Silver Pyramid (Special Jury Award)", "nominee": "Laura Mora", "film": "Killing Jesus", "country": "Colombia", "lang": "Spanish"},
    {"year": 2017, "edition": 39, "category": "Best Actor", "nominee": "Raouf Ben Amor", "film": "Tunis by Night", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2017, "edition": 39, "category": "Best Actress", "nominee": "Diamand Bou Abboud", "film": "Insyriated", "country": "Lebanon", "lang": "Arabic"},

    # 2016 - 38th Edition
    {"year": 2016, "edition": 38, "category": "Golden Pyramid (Best Film)", "nominee": "", "film": "Mimosas", "country": "Spain", "lang": "Spanish"},
    {"year": 2016, "edition": 38, "category": "Silver Pyramid (Special Jury Award)", "nominee": "Licínio Azevedo", "film": "The Train of Salt and Sugar", "country": "Mozambique", "lang": "Portuguese"},
    {"year": 2016, "edition": 38, "category": "Best Actor", "nominee": "Shakib Ben Omar", "film": "Mimosas", "country": "Spain", "lang": "Spanish"},
    {"year": 2016, "edition": 38, "category": "Best Actress", "nominee": "Nahed El Sebaï", "film": "A Day for Women", "country": "Egypt", "lang": "Arabic"},

    # 2015 - 37th Edition
    {"year": 2015, "edition": 37, "category": "Golden Pyramid (Best Film)", "nominee": "", "film": "Mediterranea", "country": "Italy", "lang": "Italian"},
    {"year": 2015, "edition": 37, "category": "Silver Pyramid (Special Jury Award)", "nominee": "Dalibor Matanić", "film": "The High Sun", "country": "Croatia", "lang": "Croatian"},
    {"year": 2015, "edition": 37, "category": "Best Actor", "nominee": "Mustafa Shakir", "film": "Mediterranea", "country": "Italy", "lang": "Italian"},
    {"year": 2015, "edition": 37, "category": "Best Actress", "nominee": "Louise Bourgoin", "film": "I Am a Soldier", "country": "France", "lang": "French"},

    # 2014 - 36th Edition
    {"year": 2014, "edition": 36, "category": "Golden Pyramid (Best Film)", "nominee": "", "film": "Melbourne", "country": "Iran", "lang": "Farsi"},
    {"year": 2014, "edition": 36, "category": "Silver Pyramid (Special Jury Award)", "nominee": "Kristina Grozeva, Petar Valchanov", "film": "The Lesson", "country": "Bulgaria", "lang": "Bulgarian"},
    {"year": 2014, "edition": 36, "category": "Best Actor", "nominee": "Khaled Abol Naga", "film": "Eyes of Thieves", "country": "Palestine", "lang": "Arabic"},
    {"year": 2014, "edition": 36, "category": "Best Actress", "nominee": "Adele Haenel", "film": "Love at First Fight", "country": "France", "lang": "French"},

    # 2012 - 35th Edition
    {"year": 2012, "edition": 35, "category": "Golden Pyramid (Best Film)", "nominee": "", "film": "Rendez-vous in Kiruna", "country": "France", "lang": "French"},
    {"year": 2012, "edition": 35, "category": "Silver Pyramid (Special Jury Award)", "nominee": "Massoud Bakhshi", "film": "A Respectable Family", "country": "Iran", "lang": "Farsi"},

    # 2010 - 34th Edition
    {"year": 2010, "edition": 34, "category": "Golden Pyramid (Best Film)", "nominee": "", "film": "Lust", "country": "Egypt", "lang": "Arabic"},
    {"year": 2010, "edition": 34, "category": "Silver Pyramid (Special Jury Award)", "nominee": "Bertrand Blier", "film": "The Clink of Ice", "country": "France", "lang": "French"},
    {"year": 2010, "edition": 34, "category": "Best Actor", "nominee": "Amr Waked", "film": "Lust", "country": "Egypt", "lang": "Arabic"},
    {"year": 2010, "edition": 34, "category": "Best Actress", "nominee": "Sawsan Badr", "film": "Lust", "country": "Egypt", "lang": "Arabic"}
]

CSV_PATH = os.path.join(os.path.dirname(__file__), "cairo_iff_awards.csv")
CEREMONY_NAME = "Cairo International Film Festival Awards"
CEREMONY_SLUG = "cairo-iff"
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
        VALUES (%s, %s, %s, 1976)
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
