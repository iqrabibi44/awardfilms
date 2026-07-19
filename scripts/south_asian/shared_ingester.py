"""
scripts/south_asian/shared_ingester.py
Shared logic for Wikipedia scraping (MySQL version).
"""
import os
import sys
import re
import mysql.connector
from bs4 import BeautifulSoup

try:
    from slugify import slugify
except ImportError:
    def slugify(t):
        import unicodedata
        t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
        return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", t.lower())).strip("-")

# Add project root to sys.path so we can import lib.text_spinner
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))
from lib.text_spinner import TextParaphraser

def get_db():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="",
        database="awardfilms_db",
        charset="utf8mb4",
        use_unicode=True,
        autocommit=True
    )

def get_ceremony_id(conn, slug):
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM ceremonies WHERE slug = %s", (slug,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        cur.close()

def upsert_edition(conn, ceremony_id, year, base_year, prefix):
    edition_num = year - base_year + 1
    slug = f"{prefix}-{year}"
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO editions (ceremony_id, edition_number, year, slug)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE slug = VALUES(slug)
            """,
            (ceremony_id, edition_num, year, slug),
        )
        cur.execute(
            "SELECT id FROM editions WHERE ceremony_id = %s AND year = %s",
            (ceremony_id, year)
        )
        return cur.fetchone()[0]
    finally:
        cur.close()

def upsert_category(conn, ceremony_id, slug, name, dept, is_craft=False):
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO categories (ceremony_id, slug, name, department, is_craft)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE name = VALUES(name), department = VALUES(department)
            """,
            (ceremony_id, slug, name, dept, int(is_craft)),
        )
        cur.execute(
            "SELECT id FROM categories WHERE ceremony_id = %s AND slug = %s",
            (ceremony_id, slug)
        )
        return cur.fetchone()[0]
    finally:
        cur.close()

def upsert_film(conn, title, year, country, language):
    film_slug = slugify(f"{title} {year}")
    if not film_slug: return None
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO films (slug, title, year, country, language)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE title = VALUES(title)
            """,
            (film_slug, title, year, country, language),
        )
        cur.execute(
            "SELECT id FROM films WHERE slug = %s",
            (film_slug,)
        )
        return cur.fetchone()[0]
    finally:
        cur.close()

def upsert_nomination(conn, edition_id, category_id, film_id, nominee_text, is_winner, source):
    # Paraphrase using the local dictionary TextParaphraser
    try:
        paraphraser = TextParaphraser()
        nominee_text = paraphraser.paraphrase(nominee_text)
    except Exception:
        pass
        
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT IGNORE INTO nominations
                (edition_id, category_id, film_id, person_id, nominee_text, is_winner, source_ref)
            VALUES (%s, %s, %s, NULL, %s, %s, %s)
            """,
            (edition_id, category_id, film_id, nominee_text, int(is_winner), source),
        )
    finally:
        cur.close()

def clean_cell(cell):
    if not cell: return ""
    for s in cell.find_all(["sup", "span"]): s.decompose()
    return re.sub(r"\[[\w\s]+\]", "", cell.get_text(" ", strip=True)).strip()

def parse_standard_wikitable(html, winner_classes=("success", "yes", "winner")):
    soup = BeautifulSoup(html, "lxml")
    records = []
    
    for table in soup.find_all("table", class_=re.compile("wikitable")):
        rows = table.find_all("tr")
        if len(rows) < 2: continue
        
        headers = [clean_cell(th).lower() for th in rows[0].find_all(["th", "td"])]
        
        year_col = next((i for i, h in enumerate(headers) if "year" in h), 0)
        film_col = next((i for i, h in enumerate(headers) if h in ("film", "films", "movie")), None)
        person_col = next((i for i, h in enumerate(headers) if any(k in h for k in ("recipient", "winner", "director", "actor", "actress", "name", "nominee"))), None)
        
        current_year = None
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if not cells: continue
            
            y_text = clean_cell(cells[year_col]) if year_col < len(cells) else ""
            m = re.search(r"(19|20)\d{2}", y_text)
            if m: current_year = int(m.group())
            if not current_year: continue
            
            film = clean_cell(cells[film_col]).strip("'\"") if film_col is not None and film_col < len(cells) else ""
            nominee = clean_cell(cells[person_col]) if person_col is not None and person_col < len(cells) else ""
            
            if not film and not nominee: continue
            
            cls = " ".join(row.get("class", []))
            is_winner = any(c in cls for c in winner_classes)
            
            records.append({
                "year": current_year,
                "film": film or nominee,
                "nominee": nominee or film,
                "is_winner": is_winner
            })
            
    if records and not any(r["is_winner"] for r in records):
        seen = set()
        for r in records:
            if r["year"] not in seen:
                r["is_winner"] = True
                seen.add(r["year"])
                
    return records
