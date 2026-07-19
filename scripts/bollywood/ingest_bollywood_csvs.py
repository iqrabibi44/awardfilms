import os
import sys
import pandas as pd
from slugify import slugify

from shared_ingester import get_db, get_ceremony_id, upsert_edition, upsert_category, upsert_film, upsert_nomination

CEREMONY_MAPPING = {
    "filmfare_awards.csv": {"slug": "filmfare", "prefix": "filmfare", "founded": 1954},
    "iifa_awards.csv": {"slug": "iifa", "prefix": "iifa", "founded": 2000},
    "national_awards.csv": {"slug": "national-film-awards-india", "prefix": "national", "founded": 1954},
    "screen_awards.csv": {"slug": "screen-awards", "prefix": "screen", "founded": 1994},
    "zee_cine_awards.csv": {"slug": "zee-cine-awards", "prefix": "zee", "founded": 1998},
    "stardust_awards.csv": {"slug": "stardust-awards", "prefix": "stardust", "founded": 2004},
    "producers_guild_awards.csv": {"slug": "producers-guild", "prefix": "guild", "founded": 2004},
}

def determine_dept(category_name):
    cat_lower = str(category_name).lower()
    if "director" in cat_lower or "direction" in cat_lower:
        return "Directing"
    if "actor" in cat_lower or "actress" in cat_lower or "star" in cat_lower:
        return "Acting"
    if "music" in cat_lower or "singer" in cat_lower or "playback" in cat_lower:
        return "Music"
    if "film" in cat_lower or "movie" in cat_lower or "picture" in cat_lower:
        return "Film"
    if "cinematography" in cat_lower or "editing" in cat_lower or "design" in cat_lower:
        return "Craft"
    if "story" in cat_lower or "screenplay" in cat_lower or "writer" in cat_lower:
        return "Writing"
    return "Other"

def main():
    conn = get_db()
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    
    total_nominations = 0
    for filename, meta in CEREMONY_MAPPING.items():
        filepath = os.path.join(output_dir, filename)
        if not os.path.exists(filepath):
            print(f"Skipping {filename} (not found)")
            continue
            
        print(f"\n[*] Processing {meta['slug']} from {filename}...")
        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            print(f"  Error reading CSV: {e}")
            continue
            
        if df.empty:
            print(f"  No records in {filename}")
            continue
            
        ceremony_id = get_ceremony_id(conn, meta["slug"])
        nom_count = 0
        
        for _, row in df.iterrows():
            # Oscar schema: year_film, year_ceremony, ceremony, category, canon_category, name, film, winner
            # Alternatively: Year, Category, Winner, Film, Name (etc.)
            year_val = row.get("year_film") if pd.notna(row.get("year_film")) else row.get("Year")
            if pd.isna(year_val):
                continue
            year = int(float(year_val))
            
            cat_name = row.get("category") if pd.notna(row.get("category")) else row.get("Category")
            cat_name = str(cat_name) if pd.notna(cat_name) else "Unknown"
            
            winner_val = row.get("winner") if pd.notna(row.get("winner")) else row.get("Winner")
            winner_bool = True if str(winner_val).lower() in ['true', '1', 'winner', 'yes'] else False
            
            person_name = row.get("name") if pd.notna(row.get("name")) else row.get("Name")
            person_name = str(person_name) if pd.notna(person_name) else ""
            
            film_title = row.get("film") if pd.notna(row.get("film")) else row.get("Film")
            film_title = str(film_title) if pd.notna(film_title) else ""
            
            # Upsert Edition
            edition_id = upsert_edition(conn, ceremony_id, year, meta["founded"], meta["prefix"])
            
            # Upsert Category
            cat_slug = f"{meta['prefix']}-{slugify(cat_name)}"
            dept = determine_dept(cat_name)
            is_craft = (dept in ["Craft", "Music"])
            category_id = upsert_category(conn, ceremony_id, cat_slug, cat_name, dept, is_craft)
            
            # Upsert Film
            film_id = None
            if film_title:
                film_id = upsert_film(conn, film_title, year)
            
            # Upsert Nomination
            nominee_text = person_name if person_name else film_title
            
            upsert_nomination(conn, edition_id, category_id, film_id, None, nominee_text, is_winner=winner_bool, source_ref="Oscar Schema CSV")
            nom_count += 1
            
        print(f"  Inserted {nom_count} records for {meta['slug']}")
        total_nominations += nom_count
        
    conn.commit()
    conn.close()
    print(f"\n[+] Total nominations inserted: {total_nominations}")

if __name__ == "__main__":
    main()
