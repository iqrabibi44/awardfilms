"""
scripts/nollywood/ingest_amaa.py
Scrapes Wikipedia for African Movie Academy Awards (AMAA) history (2005–present).

Categories scraped:
  Best Film, Best Director, Best Actor, Best Actress

Usage:
  python scripts/nollywood/ingest_amaa.py
"""
import os
import sys
import re
import time
import logging
import argparse
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
LOG_DIR  = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "nollywood_errors.log"),
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
)

WIKI_BASE = "https://en.wikipedia.org/wiki/"
HEADERS   = {"User-Agent": "AwardFilms-Bot/1.0 (https://awardfilms.com)"}
CEREMONY_SLUG = "amaa"

AMAA_CATEGORIES = [
    {"name": "Best Film",     "slug": "amaa-best-film",     "wiki": "Africa_Movie_Academy_Award_for_Best_Film",     "dept": "Other"},
    {"name": "Best Director", "slug": "amaa-best-director", "wiki": "Africa_Movie_Academy_Award_for_Best_Director", "dept": "Directing"},
    {"name": "Best Actor",    "slug": "amaa-best-actor",    "wiki": "Africa_Movie_Academy_Award_for_Best_Actor_in_a_Leading_Role", "dept": "Acting"},
    {"name": "Best Actress",  "slug": "amaa-best-actress",  "wiki": "Africa_Movie_Academy_Award_for_Best_Actress_in_a_Leading_Role", "dept": "Acting"},
]

def get_db():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL not set"); sys.exit(1)
    return psycopg2.connect(url)

def get_ceremony_id(conn, slug):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM ceremonies WHERE slug = %s", (slug,))
        row = cur.fetchone()
        return row[0] if row else None

def upsert_edition(conn, ceremony_id, year):
    edition_num = year - 2004
    slug = f"amaa-{year}"
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO editions (ceremony_id, edition_number, year, slug)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (ceremony_id, year) DO UPDATE SET slug = EXCLUDED.slug
            RETURNING id
            """,
            (ceremony_id, edition_num, year, slug),
        )
        conn.commit()
        return cur.fetchone()[0]

def upsert_category(conn, ceremony_id, slug, name, dept):
    is_craft = dept not in ("Acting", "Directing", "Writing", "Other")
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO categories (ceremony_id, slug, name, department, is_craft)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ceremony_id, slug) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (ceremony_id, slug, name, dept, is_craft),
        )
        conn.commit()
        return cur.fetchone()[0]

def upsert_film(conn, title, year):
    film_slug = slugify(f"{title} {year}")
    if not film_slug: return None
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO films (slug, title, year, country, language)
            VALUES (%s, %s, %s, 'Nigeria', 'English')
            ON CONFLICT (slug) DO UPDATE SET title = EXCLUDED.title
            RETURNING id
            """,
            (film_slug, title, year),
        )
        conn.commit()
        return cur.fetchone()[0]

def upsert_nomination(conn, edition_id, category_id, film_id, nominee_text, is_winner, source):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO nominations
                (edition_id, category_id, film_id, person_id, nominee_text, is_winner, source_ref)
            VALUES (%s, %s, %s, NULL, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (edition_id, category_id, film_id, nominee_text, is_winner, source),
        )
        conn.commit()

def clean_cell(cell):
    if not cell: return ""
    for s in cell.find_all(["sup", "span"]): s.decompose()
    return re.sub(r"\[[\w\s]+\]", "", cell.get_text(" ", strip=True)).strip()

def parse_amaa_table(html):
    soup = BeautifulSoup(html, "lxml")
    records = []
    
    for table in soup.find_all("table", class_=re.compile("wikitable")):
        rows = table.find_all("tr")
        if len(rows) < 2: continue
        
        headers = [clean_cell(th).lower() for th in rows[0].find_all(["th", "td"])]
        if not any(h in ("year", "film", "winner", "recipient", "director", "actor", "actress") for h in headers):
            continue
            
        year_col = next((i for i, h in enumerate(headers) if "year" in h), 0)
        film_col = next((i for i, h in enumerate(headers) if h in ("film", "films", "movie")), None)
        person_col = next((i for i, h in enumerate(headers) if any(k in h for k in ("recipient", "winner", "director", "actor", "actress", "name", "nominee"))), None)
        
        current_year = None
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if not cells: continue
            
            y_text = clean_cell(cells[year_col]) if year_col < len(cells) else ""
            m = re.search(r"(20)\d{2}", y_text)
            if m: current_year = int(m.group())
            if not current_year: continue
            
            film = clean_cell(cells[film_col]).strip("'\"") if film_col is not None and film_col < len(cells) else ""
            nominee = clean_cell(cells[person_col]) if person_col is not None and person_col < len(cells) else ""
            
            if not film and not nominee: continue
            
            cls = " ".join(row.get("class", []))
            is_winner = any(c in cls for c in ("success", "yes", "winner"))
            
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

def main():
    conn = get_db()
    cid = get_ceremony_id(conn, CEREMONY_SLUG)
    if not cid: return

    total = 0
    editions, categories = {}, {}

    for cat in tqdm(AMAA_CATEGORIES, desc="AMAA Categories"):
        if cat["slug"] not in categories:
            categories[cat["slug"]] = upsert_category(conn, cid, cat["slug"], cat["name"], cat["dept"])
        
        r = requests.get(WIKI_BASE + cat["wiki"], headers=HEADERS)
        if r.status_code != 200: continue
        
        recs = parse_amaa_table(r.text)
        n = 0
        for rec in recs:
            if rec["year"] not in editions:
                editions[rec["year"]] = upsert_edition(conn, cid, rec["year"])
                
            fid = upsert_film(conn, rec["film"], rec["year"])
            source = f"wikipedia:amaa:{cat['wiki']}:{rec['year']}"
            upsert_nomination(conn, editions[rec["year"]], categories[cat["slug"]], fid, rec["nominee"], rec["is_winner"], source)
            n += 1
            
        total += n
        time.sleep(0.5)

    conn.close()
    print(f"AMAA complete: {total} records.")

if __name__ == "__main__":
    main()
