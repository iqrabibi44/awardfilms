import os
import sys
import pandas as pd

# Path to shared_ingester
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "bollywood")))
from shared_ingester import get_db, get_ceremony_id, upsert_edition, upsert_category, upsert_film, upsert_nomination, slugify

def determine_dept(category_name):
    cat_lower = str(category_name).lower()
    if "director" in cat_lower or "direction" in cat_lower:
        return "Directing"
    if "actor" in cat_lower or "actress" in cat_lower or "star" in cat_lower or "performance" in cat_lower or "role" in cat_lower:
        return "Acting"
    if "music" in cat_lower or "score" in cat_lower or "song" in cat_lower:
        return "Music"
    if "picture" in cat_lower or "film" in cat_lower:
        return "Film"
    if "screenplay" in cat_lower or "writing" in cat_lower:
        return "Writing"
    if "television" in cat_lower or "series" in cat_lower:
        return "Television"
    return "Other"

def main():
    conn = get_db()
    csv_path = os.path.join(os.path.dirname(__file__), "golden_globe_awards.csv")
    
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    if df.empty:
        print("No records to ingest.")
        sys.exit(0)
        
    ceremony_id = get_ceremony_id(conn, "golden-globes")
    
    total_nominations = 0
    
    # Pre-cache to speed up
    edition_cache = {}
    category_cache = {}
    
    print(f"[*] Processing {len(df)} records for Golden Globes...")
    for idx, row in df.iterrows():
        year = int(row["year"])
        cat_name = str(row["category"])
        winner_bool = bool(int(row["winner"]))
        nominee = str(row["nominee"]) if pd.notna(row["nominee"]) else ""
        film_title = str(row["film"]) if pd.notna(row["film"]) else ""
        source_url = str(row["source_url"]) if pd.notna(row["source_url"]) else ""
        
        # Edition
        if year not in edition_cache:
            edition_cache[year] = upsert_edition(conn, ceremony_id, year, 1944, "golden-globes")
        edition_id = edition_cache[year]
        
        # Category
        cat_slug = f"golden-globes-{slugify(cat_name)}"
        if cat_slug not in category_cache:
            dept = determine_dept(cat_name)
            is_craft = (dept in ["Craft", "Music"])
            category_cache[cat_slug] = upsert_category(conn, ceremony_id, cat_slug, cat_name, dept, is_craft)
        category_id = category_cache[cat_slug]
        
        # Film
        film_id = None
        if film_title:
            # We assume country USA, language English for Golden Globes mostly
            film_id = upsert_film(conn, film_title, year, "United States", "English")
            
        # Nominee text (rephrasing is handled inside upsert_nomination via spin())
        # If nominee is empty, use film_title
        nominee_text = nominee if nominee else film_title
        
        upsert_nomination(conn, edition_id, category_id, film_id, None, nominee_text, winner_bool, source_url)
        total_nominations += 1
        
        if total_nominations % 500 == 0:
            print(f"  Inserted {total_nominations} records...")
            
    conn.close()
    print(f"[+] Successfully inserted {total_nominations} records.")

if __name__ == "__main__":
    main()
