"""
scripts/bollywood/shared_ingester.py
Shared MySQL DB helpers for all Bollywood ingestion scripts.
"""
import os
import sys
import re

import mysql.connector

# Make lib importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
try:
    from lib.text_spinner import TextParaphraser
    _paraphraser = TextParaphraser()
    def spin(text):
        return _paraphraser.paraphrase(text) if text else text
except Exception:
    def spin(text):
        return text

try:
    from slugify import slugify as _slugify
    def slugify(t):
        return _slugify(str(t))[:300]
except ImportError:
    import unicodedata
    def slugify(t):
        t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
        return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", t.lower())).strip("-")[:300]


def get_db():
    return mysql.connector.connect(
        host="127.0.0.1", port=3306, user="root", password="",
        database="awardfilms_db", charset="utf8mb4"
    )


def get_ceremony_id(conn, slug):
    cur = conn.cursor()
    cur.execute("SELECT id FROM ceremonies WHERE slug = %s", (slug,))
    row = cur.fetchone()
    cur.close()
    if not row:
        print(f"ERROR: ceremony '{slug}' not found. Run seed_ceremonies.py first.")
        sys.exit(1)
    return row[0]


_ed_cache = {}
def upsert_edition(conn, ceremony_id, year, founded_year, edition_prefix):
    key = (ceremony_id, year)
    if key in _ed_cache: return _ed_cache[key]
    ed_slug = f"{edition_prefix}-{year}"
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO editions (ceremony_id, year, slug)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE slug = VALUES(slug)
        """,
        (ceremony_id, year, ed_slug),
    )
    cur.execute(
        "SELECT id FROM editions WHERE ceremony_id = %s AND year = %s",
        (ceremony_id, year),
    )
    row = cur.fetchone()
    cur.close()
    _ed_cache[key] = row[0]
    return row[0]


_cat_cache = {}
def upsert_category(conn, ceremony_id, cat_slug, cat_name, dept, is_craft=False):
    key = (ceremony_id, cat_slug)
    if key in _cat_cache: return _cat_cache[key]
    cur = conn.cursor()
    cat_slug = cat_slug[:200]
    cat_name = cat_name[:300]
    cur.execute(
        """
        INSERT INTO categories (ceremony_id, slug, name, department, is_craft)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name       = VALUES(name),
            department = VALUES(department),
            is_craft   = VALUES(is_craft)
        """,
        (ceremony_id, cat_slug, cat_name, dept, int(is_craft)),
    )
    cur.execute(
        "SELECT id FROM categories WHERE ceremony_id = %s AND slug = %s",
        (ceremony_id, cat_slug),
    )
    row = cur.fetchone()
    cur.close()
    _cat_cache[key] = row[0]
    return row[0]


_film_cache = {}
def upsert_film(conn, title, year, country="India", language="Hindi"):
    key = (title, year)
    if key in _film_cache: return _film_cache[key]
    film_slug = slugify(f"{title} {year}")
    if not film_slug:
        return None
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO films (slug, title, year, country, language)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title    = VALUES(title),
            country  = COALESCE(films.country,  VALUES(country)),
            language = COALESCE(films.language, VALUES(language))
        """,
        (film_slug, title, year, country, language),
    )
    cur.execute("SELECT id FROM films WHERE slug = %s", (film_slug,))
    row = cur.fetchone()
    cur.close()
    val = row[0] if row else None
    _film_cache[key] = val
    return val


def upsert_nomination(conn, edition_id, category_id, film_id, person_id,
                       nominee_text, is_winner, source_ref):
    spun = spin(nominee_text) if nominee_text else nominee_text
    cur = conn.cursor()
    cur.execute(
        """
        INSERT IGNORE INTO nominations (edition_id, category_id, film_id, person_id, nominee_text, is_winner, source_ref)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (edition_id, category_id, film_id, person_id, nominee_text, int(is_winner), source_ref)
    )
    cur.close()
