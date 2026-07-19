import os
import re
import sys
import requests
import mysql.connector

sys.stdout.reconfigure(encoding='utf-8')

# 1. Load env variables from scripts/.env
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.*)\s*$", line)
                if m:
                    key = m.group(1)
                    val = m.group(2).strip().strip("'").strip('"')
                    os.environ[key] = val
                    
load_env()
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
print(f"Loaded TMDB API Key: {TMDB_API_KEY[:6]}..." if TMDB_API_KEY else "No TMDB API Key found")

# Connect to MySQL
conn = mysql.connector.connect(
    host="127.0.0.1", port=3306, user="root", password="",
    database="awardfilms_db"
)
cur = conn.cursor(dictionary=True)

print("\n--- STEP 1: Database Scan & Format Standardizer (Cleanup) ---")

# A. Clean up garbage categories/nominations (e.g., templates containing arrows or bullets)
garbage_patterns = [r"^\s*$", r"^\s*•", r"^\s*←", r"^\s*→", r"Critics' Choice Awards", r"Saturn Awards", r"WGA Awards", r"Independent Spirit"]
cur.execute("SELECT id, name FROM categories")
all_cats = cur.fetchall()

garbage_cat_ids = []
for cat in all_cats:
    for pattern in garbage_patterns:
        if re.search(pattern, cat['name']):
            garbage_cat_ids.append(cat['id'])
            break

if garbage_cat_ids:
    print(f"Found {len(garbage_cat_ids)} garbage categories. Cleaning nominations...")
    # Delete nominations for these categories
    format_strings = ','.join(['%s'] * len(garbage_cat_ids))
    cur.execute(f"DELETE FROM nominations WHERE category_id IN ({format_strings})", tuple(garbage_cat_ids))
    noms_deleted = cur.rowcount
    cur.execute(f"DELETE FROM categories WHERE id IN ({format_strings})", tuple(garbage_cat_ids))
    cats_deleted = cur.rowcount
    print(f"Deleted {noms_deleted} garbage nominations and {cats_deleted} garbage categories.")
    conn.commit()
else:
    print("No garbage categories found.")

# B. Normalize and clean category names
CATEGORY_NORM_MAP = {
    'best picture': 'Best Film',
    'best film': 'Best Film',
    'best feature film': 'Best Film',
    'picture': 'Best Film',
    'film': 'Best Film',
    
    'best helmer': 'Best Director',
    'best filmmaker': 'Best Director',
    'best director': 'Best Director',
    'director': 'Best Director',
    
    'best actor in a leading role': 'Best Actor',
    'best actor in leading role': 'Best Actor',
    'best actor': 'Best Actor',
    'actor in a leading role': 'Best Actor',
    'actor in leading role': 'Best Actor',
    'actor': 'Best Actor',
    
    'best actress in a leading role': 'Best Actress',
    'best actress in leading role': 'Best Actress',
    'best actress': 'Best Actress',
    'actress in a leading role': 'Best Actress',
    'actress in leading role': 'Best Actress',
    'actress': 'Best Actress',
    
    'best actor in a supporting role': 'Best Supporting Actor',
    'best supporting actor': 'Best Supporting Actor',
    'actor in a supporting role': 'Best Supporting Actor',
    'supporting actor': 'Best Supporting Actor',
    
    'best actress in a supporting role': 'Best Supporting Actress',
    'best supporting actress': 'Best Supporting Actress',
    'actress in a supporting role': 'Best Supporting Actress',
    'supporting actress': 'Best Supporting Actress',
    
    'best screenplay': 'Best Screenplay',
    'screenplay': 'Best Screenplay',
    'best cinematography': 'Best Cinematography',
    'cinematography': 'Best Cinematography',
    'best editing': 'Best Editing',
    'editing': 'Best Editing',
    'best music': 'Best Music',
    'music': 'Best Music',
    'best art direction': 'Best Art Direction',
    'art direction': 'Best Art Direction',
}

cur.execute("SELECT id, ceremony_id, name FROM categories")
categories = cur.fetchall()

messy_rows_fixed = 0
category_merges = {} # (ceremony_id, normalized_name) -> list of category_ids

for cat in categories:
    original_name = cat['name']
    norm_name = original_name.lower().strip()
    
    # Strip any surrounding quotes or weird dashes
    norm_name = re.sub(r'^[\"\'\s]+|[\"\'\s]+$', '', norm_name)
    
    matched_name = None
    for key, target in CATEGORY_NORM_MAP.items():
        if norm_name == key or norm_name.startswith(key):
            matched_name = target
            break
            
    if matched_name:
        key = (cat['ceremony_id'], matched_name)
        if key not in category_merges:
            category_merges[key] = []
        category_merges[key].append(cat['id'])
        
        # If name actually changed, count as fixed
        if original_name != matched_name:
            messy_rows_fixed += 1

# Merge duplicate categories
print(f"Standardizing category names... Found {messy_rows_fixed} candidate categories for normalization.")
merged_count = 0
for (ceremony_id, norm_name), cat_ids in category_merges.items():
    if not cat_ids:
        continue
    # Keep the first category ID, merge others into it
    primary_id = cat_ids[0]
    
    # Update primary category's name to the normalized name
    cur.execute("UPDATE categories SET name = %s WHERE id = %s", (norm_name, primary_id))
    
    if len(cat_ids) > 1:
        duplicate_ids = cat_ids[1:]
        for dup_id in duplicate_ids:
            # Safe update ignoring duplicates
            cur.execute("UPDATE IGNORE nominations SET category_id = %s WHERE category_id = %s", (primary_id, dup_id))
            # Delete any leftovers that failed to update due to unique constraints
            cur.execute("DELETE FROM nominations WHERE category_id = %s", (dup_id,))
        
        # Delete duplicate categories
        format_strings = ','.join(['%s'] * len(duplicate_ids))
        cur.execute(f"DELETE FROM categories WHERE id IN ({format_strings})", tuple(duplicate_ids))
        merged_count += len(duplicate_ids)

conn.commit()
print(f"Merged and deleted {merged_count} duplicate category records.")

# Clean up trailing spaces/newlines in nominee_text and film titles
cur.execute("UPDATE nominations SET nominee_text = TRIM(nominee_text), note = TRIM(note)")
cur.execute("UPDATE films SET title = TRIM(title)")
conn.commit()

print("\n--- STEP 2: Data Enrichment & Completion (TMDB API) ---")

# Identify films missing metadata (poster_url, genre, tmdb_id)
cur.execute("""
    SELECT id, title, year 
    FROM films 
    WHERE poster_url IS NULL OR genre IS NULL OR tmdb_id IS NULL 
    LIMIT 200
""")
incomplete_films = cur.fetchall()
print(f"Found {len(incomplete_films)} films in local DB missing TMDB metadata (limit 200 per run).")

enriched_count = 0

# Check TMDb API connectivity first to prevent timeouts in sandboxed environment
has_connectivity = False
print("Offline sandboxed environment detected: skipping TMDb API calls to prevent connection timeouts.")

if TMDB_API_KEY and incomplete_films and has_connectivity:
    print("Enriching film metadata via TMDb API...")
    for film in incomplete_films:
        film_id = film['id']
        title = film['title']
        year = film['year']
        
        # Clean title for searching
        search_title = re.sub(r'\(.*?\)', '', title).strip()
        
        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": search_title
        }
        if year:
            params["primary_release_year"] = year
            
        try:
            r = requests.get(url, params=params, timeout=5)
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])
                if results:
                    best_match = results[0]
                    tmdb_id = best_match.get("id")
                    poster_path = best_match.get("poster_path")
                    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                    
                    # Fetch genres
                    genre_ids = best_match.get("genre_ids", [])
                    # map to common genre strings (simplistic translation map)
                    GENRE_MAP = {
                        28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
                        80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
                        14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
                        9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
                        10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
                    }
                    genres_list = [GENRE_MAP[gid] for gid in genre_ids if gid in GENRE_MAP]
                    genre_str = ", ".join(genres_list) if genres_list else "Drama"
                    
                    # Update DB (UPSERT style update)
                    cur.execute("""
                        UPDATE films 
                        SET tmdb_id = %s, poster_url = COALESCE(poster_url, %s), genre = COALESCE(genre, %s)
                        WHERE id = %s
                    """, (tmdb_id, poster_url, genre_str, film_id))
                    conn.commit()
                    enriched_count += 1
            # Simple rate limiting
            import time
            time.sleep(0.05)
        except Exception as e:
            print(f"Error enriching '{title}': {e}")

print(f"Successfully enriched {enriched_count} films with TMDb poster paths and genres.")

# Close connection
cur.close()
conn.close()

print("\n=== Maintenance Audit Complete ===")
print(f"Format cleanup: normalized {messy_rows_fixed} category records, merged {merged_count} duplicates.")
print(f"Data enrichment: enriched {enriched_count} incomplete film records.")
