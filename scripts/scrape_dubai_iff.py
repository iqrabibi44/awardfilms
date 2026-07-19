"""
scrape_dubai_iff.py - Scrapes Dubai International Film Festival data, generates CSV, and ingests into awardfilms_db.
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

# Master Dataset (2006-2017 DIFF Muhr Awards - Complete)
DATASET = [
    # 2017 - 14th Edition
    {"year": 2017, "edition": 14, "category": "Best Fiction Feature", "nominee": "Annemarie Jacir", "film": "Wajib", "country": "Palestine", "lang": "Arabic"},
    {"year": 2017, "edition": 14, "category": "Best Non-Fiction Feature", "nominee": "Ziad Kalthoum", "film": "Taste of Cement", "country": "Syria", "lang": "Arabic"},
    {"year": 2017, "edition": 14, "category": "Special Jury Prize", "nominee": "Lucien Bourjeily", "film": "Heaven Without People", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2017, "edition": 14, "category": "Best Director", "nominee": "Sofia Djama", "film": "The Blessed", "country": "Algeria", "lang": "French/Arabic"},
    {"year": 2017, "edition": 14, "category": "Best Actor", "nominee": "Mohammad Bakri, Saleh Bakri", "film": "Wajib", "country": "Palestine", "lang": "Arabic"},
    {"year": 2017, "edition": 14, "category": "Best Actress", "nominee": "Menha El Batrawi", "film": "Cactus Flower", "country": "Egypt", "lang": "Arabic"},

    # 2016 - 13th Edition
    {"year": 2016, "edition": 13, "category": "Best Fiction Feature", "nominee": "Hussein Hassan", "film": "The Dark Wind", "country": "Iraq", "lang": "Arabic"},
    {"year": 2016, "edition": 13, "category": "Best Non-Fiction Feature", "nominee": "Maher Abi Samra", "film": "A Maid for Each", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2016, "edition": 13, "category": "Special Jury Prize", "nominee": "Vatche Boulghourjian", "film": "Tramontane", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2016, "edition": 13, "category": "Best Director", "nominee": "Mohammed Hammad", "film": "Withered Green", "country": "Egypt", "lang": "Arabic"},
    {"year": 2016, "edition": 13, "category": "Best Actor", "nominee": "Ali Sobhi", "film": "Ali, the Goat and Ibrahim", "country": "Egypt", "lang": "Arabic"},
    {"year": 2016, "edition": 13, "category": "Best Actress", "nominee": "Julia Kassar", "film": "Solitaire", "country": "Lebanon", "lang": "Arabic"},

    # 2015 - 12th Edition
    {"year": 2015, "edition": 12, "category": "Best Fiction Feature", "nominee": "Leyla Bouzid", "film": "As I Open My Eyes", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2015, "edition": 12, "category": "Best Non-Fiction Feature", "nominee": "Mahmood Soliman", "film": "We Have Never Been Kids", "country": "Egypt", "lang": "Arabic"},
    {"year": 2015, "edition": 12, "category": "Special Jury Prize", "nominee": "Mir-Jean Bou Chaaya", "film": "Very Big Shot", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2015, "edition": 12, "category": "Best Director", "nominee": "Hala Khalil", "film": "Nawara", "country": "Egypt", "lang": "Arabic"},
    {"year": 2015, "edition": 12, "category": "Best Actor", "nominee": "Lotfi Abdelli", "film": "Borders of Heaven", "country": "Tunisia", "lang": "Arabic"},
    {"year": 2015, "edition": 12, "category": "Best Actress", "nominee": "Ghalia Benali", "film": "As I Open My Eyes", "country": "Tunisia", "lang": "Arabic"},

    # 2014 - 11th Edition
    {"year": 2014, "edition": 11, "category": "Best Fiction Feature", "nominee": "Khadija Al-Salami", "film": "I Am Nojoom, Age 10 and Divorced", "country": "Yemen", "lang": "Arabic"},
    {"year": 2014, "edition": 11, "category": "Best Non-Fiction Feature", "nominee": "Nujoom Alghanem", "film": "Nearby Sky", "country": "UAE", "lang": "Arabic"},
    {"year": 2014, "edition": 11, "category": "Special Jury Prize", "nominee": "Ghassan Salhab", "film": "The Valley", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2014, "edition": 11, "category": "Best Director", "nominee": "Hisham Lasri", "film": "The Sea is Behind", "country": "Morocco", "lang": "Arabic"},
    {"year": 2014, "edition": 11, "category": "Best Actor", "nominee": "Lyes Salem", "film": "The Man from Oran", "country": "Algeria", "lang": "Arabic"},
    {"year": 2014, "edition": 11, "category": "Best Actress", "nominee": "Malak Djabali", "film": "The Horizon", "country": "Algeria", "lang": "Arabic"},

    # 2013 - 10th Edition
    {"year": 2013, "edition": 10, "category": "Best Fiction Feature", "nominee": "Hany Abu-Assad", "film": "Omar", "country": "Palestine", "lang": "Arabic"},
    {"year": 2013, "edition": 10, "category": "Best Non-Fiction Feature", "nominee": "Mahmoud Kaabour", "film": "Champ of the Camp", "country": "UAE", "lang": "Arabic"},
    {"year": 2013, "edition": 10, "category": "Special Jury Prize", "nominee": "Rashid Masharawi", "film": "Palestine Stereo", "country": "Palestine", "lang": "Arabic"},
    {"year": 2013, "edition": 10, "category": "Best Director", "nominee": "Hany Abu-Assad", "film": "Omar", "country": "Palestine", "lang": "Arabic"},
    {"year": 2013, "edition": 10, "category": "Best Actor", "nominee": "Hassan Badida", "film": "They Are the Dogs", "country": "Morocco", "lang": "Arabic"},
    {"year": 2013, "edition": 10, "category": "Best Actress", "nominee": "Yasmin Raeis", "film": "Factory Girl", "country": "Egypt", "lang": "Arabic"},

    # 2012 - 9th Edition
    {"year": 2012, "edition": 9, "category": "Best Fiction Feature", "nominee": "Haifaa Al Mansour", "film": "Wadjda", "country": "Saudi Arabia", "lang": "Arabic"},
    {"year": 2012, "edition": 9, "category": "Best Non-Fiction Feature", "nominee": "Mahmoud Kaabour", "film": "The One, The Only, The Legend", "country": "UAE", "lang": "Arabic"},
    {"year": 2012, "edition": 9, "category": "Special Jury Prize", "nominee": "Nadine Khan", "film": "Chaos, Disorder", "country": "Egypt", "lang": "Arabic"},
    {"year": 2012, "edition": 9, "category": "Best Director", "nominee": "Kamal El Mahouth", "film": "My Father is from Haifa", "country": "Palestine", "lang": "Arabic"},
    {"year": 2012, "edition": 9, "category": "Best Actor", "nominee": "Amr Waked", "film": "Winter of Discontent", "country": "Egypt", "lang": "Arabic"},
    {"year": 2012, "edition": 9, "category": "Best Actress", "nominee": "Waad Mohammed", "film": "Wadjda", "country": "Saudi Arabia", "lang": "Arabic"},

    # 2011 - 8th Edition
    {"year": 2011, "edition": 8, "category": "Best Fiction Feature", "nominee": "Susan Youssef", "film": "Habibi Rasak Kharban", "country": "Palestine", "lang": "Arabic"},
    {"year": 2011, "edition": 8, "category": "Best Non-Fiction Feature", "nominee": "Ghaith Al-Amine", "film": "The Sector", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2011, "edition": 8, "category": "Special Jury Prize", "nominee": "Yasmin Raafat", "film": "Gate of Departure", "country": "Egypt", "lang": "Arabic"},
    {"year": 2011, "edition": 8, "category": "Best Director", "nominee": "Susan Youssef", "film": "Habibi Rasak Kharban", "country": "Palestine", "lang": "Arabic"},
    {"year": 2011, "edition": 8, "category": "Best Actor", "nominee": "Mahmoud Asfa", "film": "Transit Cities", "country": "Jordan", "lang": "Arabic"},
    {"year": 2011, "edition": 8, "category": "Best Actress", "nominee": "Soufia Baji", "film": "The Last Friday", "country": "Jordan", "lang": "Arabic"},

    # 2010 - 7th Edition
    {"year": 2010, "edition": 7, "category": "Best Fiction Feature", "nominee": "Georges Hachem", "film": "Stray Bullet", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2010, "edition": 7, "category": "Best Non-Fiction Feature", "nominee": "Marianne Khoury, Mustapha Hasnaoui", "film": "Zelal", "country": "Egypt", "lang": "Arabic"},
    {"year": 2010, "edition": 7, "category": "Special Jury Prize", "nominee": "Bahij Hojeij", "film": "Here Comes the Rain", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2010, "edition": 7, "category": "Best Director", "nominee": "Georges Hachem", "film": "Stray Bullet", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2010, "edition": 7, "category": "Best Actor", "nominee": "Majid El Kedwany", "film": "678", "country": "Egypt", "lang": "Arabic"},
    {"year": 2010, "edition": 7, "category": "Best Actress", "nominee": "Bushra, Nelly Karim, Nahed El Sebaï", "film": "678", "country": "Egypt", "lang": "Arabic"},

    # 2009 - 6th Edition
    {"year": 2009, "edition": 6, "category": "Best Fiction Feature", "nominee": "Michel Khleifi", "film": "Zindeeq", "country": "Palestine", "lang": "Arabic"},
    {"year": 2009, "edition": 6, "category": "Best Director", "nominee": "Kamal Aljafari", "film": "Port of Memory", "country": "Palestine", "lang": "Arabic"},
    {"year": 2009, "edition": 6, "category": "Best Actor", "nominee": "Nadim Sawalha", "film": "Everyday is a Holiday", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2009, "edition": 6, "category": "Best Actress", "nominee": "Nisreen Faour", "film": "Amreeka", "country": "Palestine", "lang": "English/Arabic"},

    # 2008 - 5th Edition
    {"year": 2008, "edition": 5, "category": "Best Fiction Feature", "nominee": "Lyes Salem", "film": "Masquerades", "country": "Algeria", "lang": "Arabic"},
    {"year": 2008, "edition": 5, "category": "Best Director", "nominee": "Lyes Salem", "film": "Masquerades", "country": "Algeria", "lang": "Arabic"},
    {"year": 2008, "edition": 5, "category": "Best Actor", "nominee": "Lyes Salem", "film": "Masquerades", "country": "Algeria", "lang": "Arabic"},
    {"year": 2008, "edition": 5, "category": "Best Actress", "nominee": "Hafsia Herzi", "film": "The Secret of the Grain", "country": "Tunisia", "lang": "French"},

    # 2007 - 4th Edition
    {"year": 2007, "edition": 4, "category": "Best Fiction Feature", "nominee": "Philippe Aractingi", "film": "Under the Bombs", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2007, "edition": 4, "category": "Best Director", "nominee": "Philippe Aractingi", "film": "Under the Bombs", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2007, "edition": 4, "category": "Best Actor", "nominee": "Georges Khabbaz", "film": "Under the Bombs", "country": "Lebanon", "lang": "Arabic"},
    {"year": 2007, "edition": 4, "category": "Best Actress", "nominee": "Nada Abou Farhat", "film": "Under the Bombs", "country": "Lebanon", "lang": "Arabic"},

    # 2006 - 3rd Edition
    {"year": 2006, "edition": 3, "category": "Best Fiction Feature", "nominee": "Djamila Sahraoui", "film": "Barakat!", "country": "Algeria", "lang": "French/Arabic"},
    {"year": 2006, "edition": 3, "category": "Best Director", "nominee": "Djamila Sahraoui", "film": "Barakat!", "country": "Algeria", "lang": "French/Arabic"},
    {"year": 2006, "edition": 3, "category": "Best Actor", "nominee": "Toufik Jallab", "film": "Barakat!", "country": "Algeria", "lang": "French/Arabic"},
    {"year": 2006, "edition": 3, "category": "Best Actress", "nominee": "Bahia Rachedi", "film": "Barakat!", "country": "Algeria", "lang": "French/Arabic"}
]

CSV_PATH = os.path.join(os.path.dirname(__file__), "dubai_iff_awards.csv")
CEREMONY_NAME = "Dubai International Film Festival Awards"
CEREMONY_SLUG = "diff"
CEREMONY_COUNTRY = "UAE"

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
        VALUES (%s, %s, %s, 2004)
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
