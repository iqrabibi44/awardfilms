"""
scripts/nollywood/ingest_fespaco.py
Scrapes Wikipedia for FESPACO history (1969-present).
The top prize is the Etalon de Yennenga (Grand Prize).
FESPACO is biennial.
"""
import os
import sys
import re
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

WIKI_URL = "https://en.wikipedia.org/wiki/Panafrican_Film_and_Television_Festival_of_Ouagadougou"

def get_db():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def parse_fespaco(html):
    soup = BeautifulSoup(html, "lxml")
    records = []
    
    # Etalon de Yennenga winners are usually listed in a specific section/list.
    # Looking for a list under the heading "Étalon de Yennenga"
    headings = soup.find_all(["h2", "h3"])
    for h in headings:
        if "Yennenga" in h.get_text() or "Prize" in h.get_text() or "Winners" in h.get_text():
            ul = h.find_next_sibling("ul")
            if not ul: continue
            
            for li in ul.find_all("li"):
                text = li.get_text(strip=True)
                # Format is typically "1972: Le Wazzou polygame by Oumarou Ganda (Niger)"
                m = re.search(r"^(\d{4}):?\s*([^\(by]+)(?:by\s+([^\(]+))?", text, re.IGNORECASE)
                if m:
                    year = int(m.group(1))
                    film = m.group(2).strip(" \u2013-")
                    director = m.group(3).strip(" \u2013-") if m.group(3) else film
                    
                    records.append({
                        "year": year,
                        "film": film,
                        "director": director,
                    })
    return records

def main():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM ceremonies WHERE slug = 'fespaco'")
        cid = cur.fetchone()[0]
        cur.execute("INSERT INTO categories (ceremony_id, slug, name, department) VALUES (%s, %s, %s, 'Other') ON CONFLICT DO NOTHING RETURNING id", (cid, 'fespaco-etalon-dor', "Étalon d'Or de Yennenga"))
        cat_row = cur.fetchone()
        if not cat_row:
            cur.execute("SELECT id FROM categories WHERE slug = 'fespaco-etalon-dor'")
            cat_row = cur.fetchone()
        cat_id = cat_row[0]

    r = requests.get(WIKI_URL)
    recs = parse_fespaco(r.text)
    
    n = 0
    with conn.cursor() as cur:
        for rec in tqdm(recs, desc="FESPACO"):
            # Upsert Edition
            cur.execute(
                "INSERT INTO editions (ceremony_id, year, slug) VALUES (%s, %s, %s) ON CONFLICT (ceremony_id, year) DO UPDATE SET slug = EXCLUDED.slug RETURNING id",
                (cid, rec["year"], f"fespaco-{rec['year']}")
            )
            eid = cur.fetchone()[0]
            
            # Upsert Film
            fs = slugify(f"{rec['film']} {rec['year']}")
            if not fs: continue
            cur.execute(
                "INSERT INTO films (slug, title, year, country, language) VALUES (%s, %s, %s, 'Burkina Faso', 'French') ON CONFLICT (slug) DO UPDATE SET title = EXCLUDED.title RETURNING id",
                (fs, rec["film"], rec["year"])
            )
            fid = cur.fetchone()[0]
            
            # Upsert Nomination
            cur.execute(
                "INSERT INTO nominations (edition_id, category_id, film_id, nominee_text, is_winner, source_ref) VALUES (%s, %s, %s, %s, true, 'wikipedia:fespaco') ON CONFLICT DO NOTHING",
                (eid, cat_id, fid, rec["director"])
            )
            n += 1
        conn.commit()
    conn.close()
    print(f"FESPACO complete: {n} records.")

if __name__ == "__main__":
    main()
