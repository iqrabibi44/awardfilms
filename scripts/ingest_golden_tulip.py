"""
ingest_golden_tulip.py — Ingests Golden Tulip Awards CSV into awardfilms_db
"""
import os
import sys
import re
import csv
import mysql.connector

sys.stdout.reconfigure(encoding='utf-8')

try:
    from slugify import slugify as _slugify
    def slugify(t):
        return _slugify(str(t))[:300]
except ImportError:
    import unicodedata
    def slugify(t):
        t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
        return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", t.lower())).strip("-")[:300]

CSV_PATH = os.path.join(os.path.dirname(__file__), "golden_tulip_awards.csv")
CEREMONY_NAME = "Golden Tulip Awards"
CEREMONY_SLUG = "golden-tulip-awards"   # must match navigation.php slug
CEREMONY_COUNTRY = "Turkey"

def get_db():
    return mysql.connector.connect(
        host="127.0.0.1", port=3306, user="root", password="",
        database="awardfilms_db", charset="utf8mb4"
    )

def ensure_ceremony(conn):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ceremonies (slug, name, country, founded_year)
        VALUES (%s, %s, %s, 2003)
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

def ensure_category(conn, ceremony_id, cat_name, department='Film'):
    cat_slug = slugify(f"{ceremony_id}-{cat_name}")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO categories (ceremony_id, slug, name, department)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE name=VALUES(name)
    """, (ceremony_id, cat_slug, cat_name, department))
    cur.execute("SELECT id FROM categories WHERE ceremony_id = %s AND slug = %s", (ceremony_id, cat_slug))
    row = cur.fetchone()
    cur.close()
    return row[0]

def ensure_film(conn, title, year):
    if not title or title.strip() == '':
        return None
    film_slug = slugify(f"{title} {year}")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO films (slug, title, year, country, language)
        VALUES (%s, %s, %s, 'International', 'Various')
        ON DUPLICATE KEY UPDATE title=VALUES(title)
    """, (film_slug, title.strip(), year))
    cur.execute("SELECT id FROM films WHERE slug = %s", (film_slug,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None

def main():
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    print(f"Ingesting {len(rows)} records into awardfilms_db...")

    conn = get_db()
    cur = conn.cursor()

    ceremony_id = ensure_ceremony(conn)
    print(f"Ceremony id: {ceremony_id}")

    editions = {}
    categories = {}
    films = {}
    inserted = 0

    for row in rows:
        year = int(row['Year'])
        edition_num = int(row['Edition'])
        category = row['Category']
        nominee_text = row['Nominee/Winner'].strip()
        film_title = row['Film'].strip()
        is_winner = 1 if row['Winner/Nominee Status'].lower() == 'winner' else 0

        # Edition
        ed_key = year
        if ed_key not in editions:
            editions[ed_key] = ensure_edition(conn, ceremony_id, year, edition_num)
        e_id = editions[ed_key]

        # Category
        dept = 'Film' if 'film' in category.lower() else 'General'
        cat_key = category
        if cat_key not in categories:
            categories[cat_key] = ensure_category(conn, ceremony_id, category, dept)
        cat_id = categories[cat_key]

        # Film (release year = ceremony year - 1)
        film_key = f"{film_title}-{year - 1}"
        if film_key not in films:
            films[film_key] = ensure_film(conn, film_title, year - 1)
        f_id = films[film_key]

        if not f_id:
            continue

        # Insert nomination
        cur.execute("""
            INSERT IGNORE INTO nominations
                (edition_id, category_id, film_id, nominee_text, is_winner, source_ref)
            VALUES (%s, %s, %s, %s, %s, 'Wikipedia')
        """, (e_id, cat_id, f_id, nominee_text, is_winner))
        inserted += cur.rowcount

    conn.commit()
    cur.close()
    conn.close()
    print(f"Successfully ingested {inserted} nominations into the database.")

if __name__ == '__main__':
    main()
