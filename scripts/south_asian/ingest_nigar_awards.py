"""
scripts/south_asian/ingest_nigar_awards.py
Nigar Awards ingestion (historic archive 1957-present).
Many early years have partial data.
"""
import time
import requests
import os
import logging
from tqdm import tqdm
from bs4 import BeautifulSoup
import re
from shared_ingester import get_db, get_ceremony_id, upsert_edition, upsert_category, upsert_film, upsert_nomination, clean_cell

# Set up dedicated gap logging
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "nigar_gaps.log"),
    level=logging.INFO,
    format="%(message)s"
)

WIKI_URL = "https://en.wikipedia.org/wiki/Nigar_Awards"

def parse_nigar_awards(html):
    soup = BeautifulSoup(html, "lxml")
    records = []
    
    # Nigar Wikipedia often lists winners in nested lists or a massive table per decade.
    # We will search for all wikitables and attempt to parse Year, Film, Actor, Actress, Director.
    for table in soup.find_all("table", class_=re.compile("wikitable")):
        rows = table.find_all("tr")
        if len(rows) < 2: continue
        headers = [clean_cell(th).lower() for th in rows[0].find_all(["th", "td"])]
        
        y_col = next((i for i, h in enumerate(headers) if "year" in h), 0)
        f_col = next((i for i, h in enumerate(headers) if "film" in h or "best film" in h), None)
        d_col = next((i for i, h in enumerate(headers) if "director" in h), None)
        a_col = next((i for i, h in enumerate(headers) if "actor" in h), None)
        actress_col = next((i for i, h in enumerate(headers) if "actress" in h), None)
        
        current_year = None
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if not cells: continue
            
            y_text = clean_cell(cells[y_col]) if y_col < len(cells) else ""
            m = re.search(r"(19|20)\d{2}", y_text)
            if m: current_year = int(m.group())
            if not current_year: continue
            
            # Since early years have gaps, we log them.
            if len(cells) <= 2:
                logging.info(f"GAP DETECTED: Nigar Awards {current_year} seems to have partial/missing data.")
            
            film = clean_cell(cells[f_col]) if f_col is not None and f_col < len(cells) else None
            if film: records.append({"year": current_year, "cat": "nigar-best-film", "nom": film, "film": film})
            
            director = clean_cell(cells[d_col]) if d_col is not None and d_col < len(cells) else None
            if director: records.append({"year": current_year, "cat": "nigar-best-director", "nom": director, "film": film or director})
            
            actor = clean_cell(cells[a_col]) if a_col is not None and a_col < len(cells) else None
            if actor: records.append({"year": current_year, "cat": "nigar-best-actor", "nom": actor, "film": film or actor})
            
            actress = clean_cell(cells[actress_col]) if actress_col is not None and actress_col < len(cells) else None
            if actress: records.append({"year": current_year, "cat": "nigar-best-actress", "nom": actress, "film": film or actress})
            
    return records

def main():
    conn = get_db()
    cid = get_ceremony_id(conn, "nigar-awards")
    
    cat_ids = {
        "nigar-best-film": upsert_category(conn, cid, "nigar-best-film", "Best Film", "Film"),
        "nigar-best-director": upsert_category(conn, cid, "nigar-best-director", "Best Director", "Directing"),
        "nigar-best-actor": upsert_category(conn, cid, "nigar-best-actor", "Best Actor", "Acting"),
        "nigar-best-actress": upsert_category(conn, cid, "nigar-best-actress", "Best Actress", "Acting"),
    }
    
    r = requests.get(WIKI_URL, headers={"User-Agent": "Mozilla/5.0"})
    recs = parse_nigar_awards(r.text)
    
    total = 0
    editions = {}
    for rec in tqdm(recs, desc="Nigar Awards"):
        if rec["year"] < 1957: continue
        if rec["year"] not in editions:
            editions[rec["year"]] = upsert_edition(conn, cid, rec["year"], 1957, "nigar")
            
        fid = upsert_film(conn, rec["film"], rec["year"] - 1, "Pakistan", "Urdu")
        upsert_nomination(conn, editions[rec["year"]], cat_ids[rec["cat"]], fid, rec["nom"], True, "wikipedia:nigar")
        total += 1
        
    conn.close()
    print(f"Nigar Awards complete: {total} records. Gaps logged to scripts/logs/nigar_gaps.log.")

if __name__ == "__main__":
    main()
