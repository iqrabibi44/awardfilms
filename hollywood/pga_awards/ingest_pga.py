import os
import sys
import pandas as pd

# Path to shared_ingester
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "bollywood")))
from shared_ingester import get_db, get_ceremony_id, upsert_edition, upsert_category, upsert_film, upsert_nomination, slugify

def determine_dept(category_name):
    return "Production"

def main():
    conn = get_db()
    conn.autocommit = False
    
    csv_path = os.path.join(os.path.dirname(__file__), "pga_awards.csv")
    
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    if df.empty:
        print("No records to ingest.")
        sys.exit(0)
        
    ceremony_id = get_ceremony_id(conn, "pga-awards")
    
    total_nominations = 0
    edition_cache = {}
    category_cache = {}
    
    print(f"[*] Processing {len(df)} records for Producers Guild of America Awards...")
    for idx, row in df.iterrows():
        year = int(row["year"])
        cat_name = str(row["category"])
        winner_bool = bool(int(row["winner"]))
        nominee = str(row["nominee"]) if pd.notna(row["nominee"]) else ""
        film_title = str(row["film"]) if pd.notna(row["film"]) else ""
        source_url = str(row["source_url"]) if pd.notna(row["source_url"]) else ""
        
        if year not in edition_cache:
            edition_cache[year] = upsert_edition(conn, ceremony_id, year, 1990, "pga-awards")
        edition_id = edition_cache[year]
        
        cat_slug = f"pga-awards-{slugify(cat_name)}"
        if cat_slug not in category_cache:
            dept = determine_dept(cat_name)
            category_cache[cat_slug] = upsert_category(conn, ceremony_id, cat_slug, cat_name, dept, False)
        category_id = category_cache[cat_slug]
        
        film_id = None
        if film_title:
            film_id = upsert_film(conn, film_title, year, "United States", "English")
            
        nominee_text = nominee if nominee else film_title
        
        upsert_nomination(conn, edition_id, category_id, film_id, None, nominee_text, winner_bool, source_url)
        total_nominations += 1
        
        if total_nominations % 200 == 0:
            print(f"  Inserted {total_nominations} records...")
            conn.commit()
            
    conn.commit()
    conn.close()
    print(f"[+] Successfully inserted {total_nominations} records.")

if __name__ == "__main__":
    main()
