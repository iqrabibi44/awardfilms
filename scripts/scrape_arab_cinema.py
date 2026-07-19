"""
scrape_arab_cinema.py - Scrapes Critics Awards for Arab Films data, generates CSV, and ingests into awardfilms_db.
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

# Master Dataset (10 editions, 2017-2026)
DATASET = [
    # 2026 - 10th Edition
    {"year": 2026, "edition": 10, "category": "Best Feature Film", "nominee": "", "film": "Once Upon a Time in Gaza", "country": "Palestine", "lang": "Arabic"},
    {"year": 2026, "edition": 10, "category": "Best Director", "nominee": "Cherien Dabis", "film": "All That’s Left of You", "country": "Palestine", "lang": "Arabic"},
    {"year": 2026, "edition": 10, "category": "Best Screenplay", "nominee": "Annemarie Jacir", "film": "Palestine 36", "country": "Palestine", "lang": "Arabic"},
    {"year": 2026, "edition": 10, "category": "Best Actress", "nominee": "Deborah Christelle Naney", "film": "Promised Sky", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2026, "edition": 10, "category": "Best Actor", "nominee": "Ahmed Malek", "film": "My Father’s Scent", "country": "Egypt", "lang": "Arabic"},
    {"year": 2026, "edition": 10, "category": "Best Documentary", "nominee": "Yunan", "film": "Yunan", "country": "Syria", "lang": "Arabic"},
    
    # 2025 - 9th Edition
    {"year": 2025, "edition": 9, "category": "Best Feature Film", "nominee": "", "film": "Thank You for Banking With Us!", "country": "Palestine", "lang": "Arabic"},
    {"year": 2025, "edition": 9, "category": "Best Director", "nominee": "Laila Abbas", "film": "Thank You for Banking With Us!", "country": "Palestine", "lang": "Arabic"},
    {"year": 2025, "edition": 9, "category": "Best Screenplay", "nominee": "Nabil Ayouch, Maryam Touzani", "film": "Everybody Loves Touda", "country": "Morocco", "lang": "Arabic"},
    {"year": 2025, "edition": 9, "category": "Best Actress", "nominee": "Nisrin Erradi", "film": "Everybody Loves Touda", "country": "Morocco", "lang": "Arabic"},
    {"year": 2025, "edition": 9, "category": "Best Actor", "nominee": "Adam Bessa", "film": "Ghost Trail", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2025, "edition": 9, "category": "Best Documentary", "nominee": "No Other Land", "film": "No Other Land", "country": "Palestine", "lang": "Arabic"},
    
    # 2024 - 8th Edition
    {"year": 2024, "edition": 8, "category": "Best Feature Film", "nominee": "", "film": "Goodbye Julia", "country": "Sudan", "lang": "Arabic"},
    {"year": 2024, "edition": 8, "category": "Best Director", "nominee": "Kaouther Ben Hania", "film": "Four Daughters", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2024, "edition": 8, "category": "Best Screenplay", "nominee": "Mohamed Kordofani", "film": "Goodbye Julia", "country": "Sudan", "lang": "Arabic"},
    {"year": 2024, "edition": 8, "category": "Best Actress", "nominee": "Mouna Hawa", "film": "Inshallah a Boy", "country": "Jordan", "lang": "Arabic"},
    {"year": 2024, "edition": 8, "category": "Best Actor", "nominee": "Saleh Bakri", "film": "The Teacher", "country": "Palestine", "lang": "Arabic"},
    {"year": 2024, "edition": 8, "category": "Best Documentary", "nominee": "Kaouther Ben Hania", "film": "Four Daughters", "country": "Tunisia", "lang": "Arabic"},
    
    # 2023 - 7th Edition
    {"year": 2023, "edition": 7, "category": "Best Feature Film", "nominee": "", "film": "Hanging Gardens", "country": "Iraq", "lang": "Arabic"},
    {"year": 2023, "edition": 7, "category": "Best Director", "nominee": "Youssef Chebbi", "film": "Ashkal", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2023, "edition": 7, "category": "Best Screenplay", "nominee": "Maryam Touzani, Nabil Ayouch", "film": "The Blue Caftan", "country": "Morocco", "lang": "Arabic"},
    {"year": 2023, "edition": 7, "category": "Best Actress", "nominee": "Lubna Azabal", "film": "The Blue Caftan", "country": "Morocco", "lang": "Arabic"},
    {"year": 2023, "edition": 7, "category": "Best Actor", "nominee": "Adam Bessa", "film": "Harka", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2023, "edition": 7, "category": "Best Documentary", "nominee": "Jumana Manna", "film": "Foragers", "country": "Palestine", "lang": "Arabic"},

    # 2022 - 6th Edition
    {"year": 2022, "edition": 6, "category": "Best Feature Film", "nominee": "", "film": "Feathers", "country": "Egypt", "lang": "Arabic"},
    {"year": 2022, "edition": 6, "category": "Best Director", "nominee": "Omar El Zohairy", "film": "Feathers", "country": "Egypt", "lang": "Arabic"},
    {"year": 2022, "edition": 6, "category": "Best Screenplay", "nominee": "Ahmed Amer, Omar El Zohairy", "film": "Feathers", "country": "Egypt", "lang": "Arabic"},
    {"year": 2022, "edition": 6, "category": "Best Actress", "nominee": "Maisa Abd Elhadi", "film": "Huda’s Salon", "country": "Palestine", "lang": "Arabic"},
    {"year": 2022, "edition": 6, "category": "Best Actor", "nominee": "Ali Suliman", "film": "Amira", "country": "Palestine", "lang": "Arabic"},
    {"year": 2022, "edition": 6, "category": "Best Documentary", "nominee": "Abdallah Al-Khatib", "film": "Little Palestine: Diary of a Siege", "country": "Palestine", "lang": "Arabic"},

    # 2021 - 5th Edition
    {"year": 2021, "edition": 5, "category": "Best Feature Film", "nominee": "", "film": "Gaza Mon Amour", "country": "Palestine", "lang": "Arabic"},
    {"year": 2021, "edition": 5, "category": "Best Director", "nominee": "Ameen Nayfeh", "film": "200 Meters", "country": "Palestine", "lang": "Arabic"},
    {"year": 2021, "edition": 5, "category": "Best Screenplay", "nominee": "Kaouther Ben Hania", "film": "The Man Who Sold His Skin", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2021, "edition": 5, "category": "Best Actress", "nominee": "Hiam Abbas", "film": "Gaza Mon Amour", "country": "Palestine", "lang": "Arabic"},
    {"year": 2021, "edition": 5, "category": "Best Actor", "nominee": "Ali Suliman", "film": "200 Meters", "country": "Palestine", "lang": "Arabic"},
    {"year": 2021, "edition": 5, "category": "Best Documentary", "nominee": "Mayye Zayed", "film": "Lift Like a Girl", "country": "Egypt", "lang": "Arabic"},

    # 2020 - 4th Edition
    {"year": 2020, "edition": 4, "category": "Best Feature Film", "nominee": "", "film": "It Must Be Heaven", "country": "Palestine", "lang": "Arabic"},
    {"year": 2020, "edition": 4, "category": "Best Director", "nominee": "Elia Suleiman", "film": "It Must Be Heaven", "country": "Palestine", "lang": "Arabic"},
    {"year": 2020, "edition": 4, "category": "Best Screenplay", "nominee": "Amjad Abu Alala, Yousef Ibrahim", "film": "You Will Die at Twenty", "country": "Sudan", "lang": "Arabic"},
    {"year": 2020, "edition": 4, "category": "Best Actress", "nominee": "Hend Sabry", "film": "Noura’s Dream", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2020, "edition": 4, "category": "Best Actor", "nominee": "Sami Bouajila", "film": "A Son", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2020, "edition": 4, "category": "Best Documentary", "nominee": "Suhaib Gasmelbari", "film": "Talking About Trees", "country": "Sudan", "lang": "Arabic"},

    # 2019 - 3rd Edition
    {"year": 2019, "edition": 3, "category": "Best Feature Film", "nominee": "", "film": "Yomeddine", "country": "Egypt", "lang": "Arabic"},
    {"year": 2019, "edition": 3, "category": "Best Director", "nominee": "Nadine Labaki", "film": "Capernaum", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2019, "edition": 3, "category": "Best Screenplay", "nominee": "Meryem Ben'M'Barek", "film": "Sofia", "country": "Morocco", "lang": "Arabic"},
    {"year": 2019, "edition": 3, "category": "Best Actress", "nominee": "Maha Alemi", "film": "Sofia", "country": "Morocco", "lang": "Arabic"},
    {"year": 2019, "edition": 3, "category": "Best Actor", "nominee": "Mohamed Dhrif", "film": "Weldi", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2019, "edition": 3, "category": "Best Documentary", "nominee": "Talal Derki", "film": "Of Fathers and Sons", "country": "Syria", "lang": "Arabic"},

    # 2018 - 2nd Edition
    {"year": 2018, "edition": 2, "category": "Best Feature Film", "nominee": "", "film": "Wajib", "country": "Palestine", "lang": "Arabic"},
    {"year": 2018, "edition": 2, "category": "Best Director", "nominee": "Ziad Doueiri", "film": "The Insult", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2018, "edition": 2, "category": "Best Screenplay", "nominee": "Annemarie Jacir", "film": "Wajib", "country": "Palestine", "lang": "Arabic"},
    {"year": 2018, "edition": 2, "category": "Best Actress", "nominee": "Mariam Al Ferjani", "film": "Beauty and the Dogs", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2018, "edition": 2, "category": "Best Actor", "nominee": "Mohamed Bakri", "film": "Wajib", "country": "Palestine", "lang": "Arabic"},
    {"year": 2018, "edition": 2, "category": "Best Documentary", "nominee": "Ziad Kalthoum", "film": "Taste of Cement", "country": "Syria", "lang": "Arabic"},

    # 2017 - 1st Edition
    {"year": 2017, "edition": 1, "category": "Best Feature Film", "nominee": "", "film": "In the Last Days of the City", "country": "Egypt", "lang": "Arabic"},
    {"year": 2017, "edition": 1, "category": "Best Director", "nominee": "Mohamed Diab", "film": "Clash", "country": "Egypt", "lang": "Arabic"},
    {"year": 2017, "edition": 1, "category": "Best Screenplay", "nominee": "Mohamed Diab, Khaled Diab", "film": "Clash", "country": "Egypt", "lang": "Arabic"},
    {"year": 2017, "edition": 1, "category": "Best Actress", "nominee": "Heba Ali", "film": "Withered Green", "country": "Egypt", "lang": "Arabic"},
    {"year": 2017, "edition": 1, "category": "Best Actor", "nominee": "Majd Mastoura", "film": "Inhebek Hedi", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2017, "edition": 1, "category": "Best Documentary", "nominee": "Singhin Talabani", "film": "A Footnote in Ballet History", "country": "Egypt", "lang": "Arabic"}
]

CSV_PATH = os.path.join(os.path.dirname(__file__), "arab_cinema_awards.csv")
CEREMONY_NAME = "Arab Cinema Awards"
CEREMONY_SLUG = "arab-cinema-awards"
CEREMONY_COUNTRY = "Pan-Arab"

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
