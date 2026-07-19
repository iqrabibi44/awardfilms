"""
scripts/nollywood/ingest_amvca.py
Scrapes Wikipedia for Africa Magic Viewers' Choice Awards (AMVCA) history.
Categories: Best Movie, Best Actor, Best Actress.
"""
import os
import sys
import re
import time
import requests
import psycopg2
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tqdm import tqdm

try:
    from slugify import slugify
except ImportError:
    def slugify(t):
        import unicodedata
        t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
        return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", t.lower())).strip("-")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

WIKI_BASE = "https://en.wikipedia.org/wiki/"
HEADERS   = {"User-Agent": "AwardFilms-Bot/1.0"}
CEREMONY_SLUG = "amvca"

CATEGORIES = [
    {"name": "Best Movie Overall", "slug": "amvca-best-movie", "wiki": "Africa_Magic_Viewers%27_Choice_Awards", "dept": "Other"},
]

def get_db():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def get_ceremony_id(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM ceremonies WHERE slug = %s", (CEREMONY_SLUG,))
        return cur.fetchone()[0]

def upsert_edition(conn, cid, year):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO editions (ceremony_id, edition_number, year, slug) VALUES (%s, %s, %s, %s) ON CONFLICT (ceremony_id, year) DO UPDATE SET slug = EXCLUDED.slug RETURNING id",
            (cid, year - 2012, year, f"amvca-{year}")
        )
        conn.commit()
        return cur.fetchone()[0]

def upsert_category(conn, cid, slug, name, dept):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO categories (ceremony_id, slug, name, department) VALUES (%s, %s, %s, %s) ON CONFLICT (ceremony_id, slug) DO UPDATE SET name = EXCLUDED.name RETURNING id",
            (cid, slug, name, dept)
        )
        conn.commit()
        return cur.fetchone()[0]

def upsert_film(conn, title, year):
    s = slugify(f"{title} {year}")
    if not s: return None
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO films (slug, title, year, country, language) VALUES (%s, %s, %s, 'Nigeria', 'English') ON CONFLICT (slug) DO UPDATE SET title = EXCLUDED.title RETURNING id",
            (s, title, year)
        )
        conn.commit()
        return cur.fetchone()[0]

def upsert_nomination(conn, eid, cat_id, fid, nom, is_winner):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO nominations (edition_id, category_id, film_id, nominee_text, is_winner, source_ref) VALUES (%s, %s, %s, %s, %s, 'wikipedia:amvca') ON CONFLICT DO NOTHING",
            (eid, cat_id, fid, nom, is_winner)
        )
        conn.commit()

def parse_amvca(html):
    soup = BeautifulSoup(html, "lxml")
    records = []
    
    # AMVCA wiki page has sections per year or per category.
    # This is a generalized scraper for the main AMVCA page which lists Best Movie winners.
    tables = soup.find_all("table", class_="wikitable")
    for table in tables:
        rows = table.find_all("tr")
        if not rows: continue
        headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
        
        y_col = next((i for i, h in enumerate(headers) if "year" in h), 0)
        f_col = next((i for i, h in enumerate(headers) if "film" in h or "movie" in h), None)
        d_col = next((i for i, h in enumerate(headers) if "director" in h or "winner" in h), None)
        
        if f_col is None: continue
        
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if not cells: continue
            
            y_text = cells[y_col].get_text(strip=True) if y_col < len(cells) else ""
            m = re.search(r"20\d{2}", y_text)
            if not m: continue
            year = int(m.group())
            
            film = cells[f_col].get_text(strip=True) if f_col < len(cells) else ""
            nom = cells[d_col].get_text(strip=True) if d_col is not None and d_col < len(cells) else film
            
            if not film: continue
            
            records.append({
                "year": year,
                "film": film,
                "nom": nom,
                "is_winner": True # Wiki mainly lists winners on the main page overview
            })
            
    return records

def main():
    conn = get_db()
    cid = get_ceremony_id(conn)
    cat_id = upsert_category(conn, cid, "amvca-best-movie", "Best Movie", "Other")
    
    r = requests.get(WIKI_BASE + CATEGORIES[0]["wiki"], headers=HEADERS)
    recs = parse_amvca(r.text)
    
    n = 0
    editions = {}
    for rec in tqdm(recs, desc="AMVCA"):
        if rec["year"] not in editions:
            editions[rec["year"]] = upsert_edition(conn, cid, rec["year"])
            
        fid = upsert_film(conn, rec["film"], rec["year"])
        upsert_nomination(conn, editions[rec["year"]], cat_id, fid, rec["nom"], rec["is_winner"])
        n += 1
        
    conn.close()
    print(f"AMVCA complete: {n} records.")

if __name__ == "__main__":
    main()
