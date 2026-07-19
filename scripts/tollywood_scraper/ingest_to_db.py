"""
scripts/tollywood_scraper/ingest_to_db.py
Ingests tollywood_awards_master.csv into the PostgreSQL database using optimized in-memory cache lookups.
"""
import os
import sys
import csv
import re
import time
import psycopg2
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env.local"))

def slugify(t):
    if not t:
        return ""
    import unicodedata
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
    return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", t.lower())).strip("-")

CEREMONY_METADATA = {
    "Filmfare Awards South": {
        "slug": "filmfare-awards-south",
        "name": "Filmfare Awards South",
        "short_name": "Filmfare South",
        "country": "India",
        "founded_year": 1972,
    },
    "SIIMA Awards Telugu": {
        "slug": "siima-awards-telugu",
        "name": "SIIMA Awards Telugu",
        "short_name": "SIIMA Telugu",
        "country": "India",
        "founded_year": 2012,
    },
    "SIIMA Awards Tamil": {
        "slug": "siima-awards-tamil",
        "name": "SIIMA Awards Tamil",
        "short_name": "SIIMA Tamil",
        "country": "India",
        "founded_year": 2012,
    },
    "SIIMA Awards Malayalam": {
        "slug": "siima-awards-malayalam",
        "name": "SIIMA Awards Malayalam",
        "short_name": "SIIMA Malayalam",
        "country": "India",
        "founded_year": 2012,
    },
    "Nandi Awards": {
        "slug": "nandi-awards",
        "name": "Nandi Awards",
        "short_name": "Nandi",
        "country": "India",
        "founded_year": 1964,
    },
    "CineMAA Awards": {
        "slug": "cinemaa-awards",
        "name": "CineMAA Awards",
        "short_name": "CineMAA",
        "country": "India",
        "founded_year": 2003,
    },
    "Santosham Film Awards": {
        "slug": "santosham-awards",
        "name": "Santosham Film Awards",
        "short_name": "Santosham",
        "country": "India",
        "founded_year": 2002,
    },
    "Vijay Awards": {
        "slug": "vijay-awards",
        "name": "Vijay Awards",
        "short_name": "Vijay",
        "country": "India",
        "founded_year": 2006,
    },
    "Sun Kudumbam Virudhugal": {
        "slug": "sun-kudumbam-virudhugal",
        "name": "Sun Kudumbam Virudhugal",
        "short_name": "Sun Kudumbam",
        "country": "India",
        "founded_year": 2009,
    },
    "Ananda Vikatan Cinema Awards": {
        "slug": "ananda-vikatan-awards",
        "name": "Ananda Vikatan Cinema Awards",
        "short_name": "Ananda Vikatan",
        "country": "India",
        "founded_year": 2002,
    },
    "Tamil Nadu State Film Awards": {
        "slug": "tamil-nadu-state-film-awards",
        "name": "Tamil Nadu State Film Awards",
        "short_name": "TN State Film",
        "country": "India",
        "founded_year": 1967,
    },
    "Kerala State Film Awards": {
        "slug": "kerala-state-film-awards",
        "name": "Kerala State Film Awards",
        "short_name": "Kerala State Film",
        "country": "India",
        "founded_year": 1969,
    },
    "Filmfare Awards South Malayalam": {
        "slug": "filmfare-awards-south-malayalam",
        "name": "Filmfare Awards South Malayalam",
        "short_name": "Filmfare Malayalam",
        "country": "India",
        "founded_year": 1972,
    },
    "Asianet Film Awards": {
        "slug": "asianet-film-awards",
        "name": "Asianet Film Awards",
        "short_name": "Asianet",
        "country": "India",
        "founded_year": 2009,
    },
    "Vanitha Film Awards": {
        "slug": "vanitha-film-awards",
        "name": "Vanitha Film Awards",
        "short_name": "Vanitha",
        "country": "India",
        "founded_year": 2010,
    },
    "Karnataka State Film Awards": {
        "slug": "karnataka-state-film-awards",
        "name": "Karnataka State Film Awards",
        "short_name": "Karnataka State Film",
        "country": "India",
        "founded_year": 1967,
    },
    "Filmfare Awards South Kannada": {
        "slug": "filmfare-awards-south-kannada",
        "name": "Filmfare Awards South Kannada",
        "short_name": "Filmfare Kannada",
        "country": "India",
        "founded_year": 1972,
    },
    "SIIMA Awards Kannada": {
        "slug": "siima-awards-kannada",
        "name": "SIIMA Awards Kannada",
        "short_name": "SIIMA Kannada",
        "country": "India",
        "founded_year": 2012,
    },
    "Suvarna Film Awards": {
        "slug": "suvarna-film-awards",
        "name": "Suvarna Film Awards",
        "short_name": "Suvarna",
        "country": "India",
        "founded_year": 2007,
    }
}

def get_db():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL not set in environment.")
        sys.exit(1)
    # Enable TCP Keepalive configuration for database connection stability
    conn = psycopg2.connect(
        url,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5
    )
    with conn.cursor() as cur:
        # Set a statement timeout of 30 seconds
        cur.execute("SET statement_timeout = 30000")
    return conn

def upsert_ceremony(conn, metadata, ceremony_cache):
    slug = metadata["slug"]
    if slug in ceremony_cache:
        return ceremony_cache[slug]
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO ceremonies (slug, name, short_name, country, founded_year, frequency)
            VALUES (%(slug)s, %(name)s, %(short_name)s, %(country)s, %(founded_year)s, 'annual')
            ON CONFLICT (slug) DO UPDATE SET
                name = EXCLUDED.name,
                short_name = EXCLUDED.short_name,
                country = EXCLUDED.country,
                founded_year = EXCLUDED.founded_year
            RETURNING id
        """, metadata)
        cid = cur.fetchone()[0]
        ceremony_cache[slug] = cid
        return cid

def upsert_edition(conn, ceremony_id, year, ceremony_slug, edition_cache):
    key = (ceremony_id, year)
    if key in edition_cache:
        return edition_cache[key]
    slug = f"{ceremony_slug}-{year}"
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO editions (ceremony_id, year, slug)
            VALUES (%s, %s, %s)
            ON CONFLICT (ceremony_id, year) DO UPDATE SET
                slug = EXCLUDED.slug
            RETURNING id
        """, (ceremony_id, year, slug))
        eid = cur.fetchone()[0]
        edition_cache[key] = eid
        return eid

def get_department(category_name):
    cat_lower = category_name.lower()
    if any(k in cat_lower for k in ("film", "picture", "movie")):
        return "Film"
    if "director" in cat_lower:
        return "Directing"
    if any(k in cat_lower for k in ("actor", "actress", "comedian", "villain", "debut", "supporting")):
        return "Acting"
    if any(k in cat_lower for k in ("music", "singer", "playback", "lyricist", "composer", "song")):
        return "Music"
    if "cinematographer" in cat_lower or "cinematography" in cat_lower:
        return "Cinematography"
    if "writer" in cat_lower or "story" in cat_lower or "screenplay" in cat_lower or "dialogue" in cat_lower:
        return "Writing"
    return "General"

def upsert_category(conn, ceremony_id, name, ceremony_slug, category_cache):
    name_truncated = name[:290]
    slug = f"{ceremony_slug}-{slugify(name_truncated)}"[:190]
    key = (ceremony_id, slug)
    if key in category_cache:
        return category_cache[key]
    dept = get_department(name_truncated)
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO categories (ceremony_id, slug, name, department, is_craft)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ceremony_id, slug) DO UPDATE SET
                name = EXCLUDED.name,
                department = EXCLUDED.department
            RETURNING id
        """, (ceremony_id, slug, name_truncated, dept, dept not in ("Acting", "Directing", "Writing", "Film")))
        cat_id = cur.fetchone()[0]
        category_cache[key] = cat_id
        return cat_id

def upsert_film(conn, title, year, film_cache, language="Telugu"):
    if not title or title.lower() in ("unspecified", "unknown", "none", "see source", "see source)", "(see source)"):
        return None
    title_truncated = title[:490]
    film_slug = slugify(f"{title_truncated} {year}")[:290]
    if not film_slug:
        return None
    if film_slug in film_cache:
        return film_cache[film_slug]
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO films (slug, title, year, country, language)
            VALUES (%s, %s, %s, 'India', %s)
            ON CONFLICT (slug) DO UPDATE SET
                title = EXCLUDED.title,
                year = EXCLUDED.year
            RETURNING id
        """, (film_slug, title_truncated, year, language))
        fid = cur.fetchone()[0]
        film_cache[film_slug] = fid
        return fid

def upsert_person(conn, name, person_cache):
    if not name or name.lower() in ("unspecified", "unknown", "none"):
        return None
    name_truncated = name[:290]
    person_slug = slugify(name_truncated)[:290]
    if not person_slug:
        return None
    if person_slug in person_cache:
        return person_cache[person_slug]
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO persons (slug, name, nationality)
            VALUES (%s, %s, 'Indian')
            ON CONFLICT (slug) DO UPDATE SET
                name = EXCLUDED.name
            RETURNING id
        """, (person_slug, name_truncated))
        pid = cur.fetchone()[0]
        person_cache[person_slug] = pid
        return pid

def insert_nomination(conn, edition_id, category_id, film_id, person_id, nominee_text, is_winner, note, source_ref, nomination_cache):
    nominee_text_truncated = nominee_text[:490]
    note_truncated = note[:490] if note else None
    key = (edition_id, category_id, nominee_text_truncated)
    
    if key in nomination_cache:
        current_is_winner = nomination_cache[key]
        if current_is_winner != is_winner:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE nominations
                    SET is_winner = %s
                    WHERE edition_id = %s AND category_id = %s AND nominee_text = %s
                """, (is_winner, edition_id, category_id, nominee_text_truncated))
            nomination_cache[key] = is_winner
            return "updated"
        return "skipped"
        
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO nominations (edition_id, category_id, film_id, person_id, nominee_text, is_winner, note, source_ref)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (edition_id, category_id, film_id, person_id, nominee_text_truncated, is_winner, note_truncated, source_ref))
    nomination_cache[key] = is_winner
    return "inserted"

def main():
    # Support custom CSV path via command-line argument
    if len(sys.argv) > 1:
        csv_path = os.path.abspath(sys.argv[1])
    else:
        csv_path = os.path.join(os.path.dirname(__file__), "output", "tollywood_awards_master.csv")
        
    if not os.path.exists(csv_path):
        print(f"ERROR: master CSV file not found at {csv_path}")
        sys.exit(1)

    while True:
        try:
            print("Connecting to database...")
            conn = get_db()

            # Load caches
            print("Pre-loading caches from database to speed up ingestion...")
            ceremony_cache = {}
            with conn.cursor() as cur:
                cur.execute("SELECT slug, id FROM ceremonies")
                for slug, cid in cur.fetchall():
                    ceremony_cache[slug] = cid

            edition_cache = {}
            with conn.cursor() as cur:
                cur.execute("SELECT id, ceremony_id, year FROM editions")
                for eid, cid, year in cur.fetchall():
                    edition_cache[(cid, year)] = eid

            category_cache = {}
            with conn.cursor() as cur:
                cur.execute("SELECT id, ceremony_id, slug FROM categories")
                for cat_id, cid, slug in cur.fetchall():
                    category_cache[(cid, slug)] = cat_id

            film_cache = {}
            with conn.cursor() as cur:
                cur.execute("SELECT id, slug FROM films")
                for fid, slug in cur.fetchall():
                    film_cache[slug] = fid

            person_cache = {}
            with conn.cursor() as cur:
                cur.execute("SELECT id, slug FROM persons")
                for pid, slug in cur.fetchall():
                    person_cache[slug] = pid

            nomination_cache = {}
            with conn.cursor() as cur:
                cur.execute("SELECT edition_id, category_id, nominee_text, is_winner FROM nominations")
                for eid, cat_id, nominee_text, is_winner in cur.fetchall():
                    nomination_cache[(eid, cat_id, nominee_text)] = is_winner
                    
            print(f"Loaded {len(ceremony_cache)} ceremonies, {len(edition_cache)} editions, {len(category_cache)} categories, {len(film_cache)} films, {len(person_cache)} persons, and {len(nomination_cache)} existing nominations.")
            
            # Seed ceremonies
            ceremony_ids = {}
            for show_name, meta in CEREMONY_METADATA.items():
                cid = upsert_ceremony(conn, meta, ceremony_cache)
                ceremony_ids[show_name] = cid

            # Read CSV and import records
            print("Ingesting nominations...")
            total_rows = 0
            total_inserted = 0
            total_updated = 0
            
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total_rows += 1
                    award_show = row["award_show"]
                    year_str = row["year"]
                    category = row["category"]
                    nominee_name = row["nominee_name"].strip()
                    work_title = row["work_title"].strip()
                    role_or_character = row["role_or_character"].strip()
                    result = row["result"]
                    source_url = row["source_url"]

                    # Parse year into integer
                    year_match = re.search(r"\d{4}", year_str)
                    if not year_match:
                        continue
                    year = int(year_match.group(0))

                    # Route dynamically by language for multi-regional award shows
                    language_clean = row.get("language", "").strip().lower()
                    if award_show == "SIIMA Awards":
                        if language_clean == "tamil":
                            award_show = "SIIMA Awards Tamil"
                        elif language_clean == "malayalam":
                            award_show = "SIIMA Awards Malayalam"
                        elif language_clean == "kannada":
                            award_show = "SIIMA Awards Kannada"
                        else:
                            award_show = "SIIMA Awards Telugu"
                    elif award_show == "Filmfare Awards South":
                        if language_clean == "malayalam":
                            award_show = "Filmfare Awards South Malayalam"
                        elif language_clean == "kannada":
                            award_show = "Filmfare Awards South Kannada"

                    ceremony_id = ceremony_ids.get(award_show)
                    if not ceremony_id:
                        ceremony_slug = slugify(award_show)
                        if ceremony_slug in ceremony_cache:
                            ceremony_id = ceremony_cache[ceremony_slug]
                        else:
                            continue
                    
                    ceremony_slug = CEREMONY_METADATA.get(award_show, {}).get("slug", slugify(award_show))

                    # Upsert Edition
                    edition_id = upsert_edition(conn, ceremony_id, year, ceremony_slug, edition_cache)

                    # Upsert Category
                    category_id = upsert_category(conn, ceremony_id, category, ceremony_slug, category_cache)

                    # Resolve nominee / film structures
                    is_film_cat = category.lower() in (
                        "best film", "best feature-film", "best feature film", "critics best film"
                    )

                    film_title = nominee_name if is_film_cat else work_title
                    person_name = None if is_film_cat else nominee_name

                    # Clean names
                    if film_title:
                        film_title = re.sub(r"\s+", " ", film_title).strip("'\" ")
                    if person_name:
                        person_name = re.sub(r"\s+", " ", person_name).strip("'\" ")

                    # Upsert Film
                    film_id = None
                    if film_title:
                        film_year = year - 1
                        film_id = upsert_film(conn, film_title, film_year, film_cache)

                    # Upsert Person (only if not a film category)
                    person_id = None
                    if person_name:
                        person_id = upsert_person(conn, person_name, person_cache)

                    # Form nominee text
                    if person_name and film_title:
                        nominee_text = f"{person_name} — {film_title}"
                    elif person_name:
                        nominee_text = person_name
                    elif film_title:
                        nominee_text = film_title
                    else:
                        nominee_text = "Unknown"

                    # Clean and set character role in note column
                    note = role_or_character if role_or_character else None
                    is_winner = result.lower() == "winner"

                    # Reference Source
                    source_ref = f"wikipedia:tollywood:{ceremony_slug}:{year}"

                    # Insert Nomination
                    status = insert_nomination(conn, edition_id, category_id, film_id, person_id, nominee_text, is_winner, note, source_ref, nomination_cache)
                    if status == "inserted":
                        total_inserted += 1
                        if (total_inserted + total_updated) % 100 == 0:
                            conn.commit()
                            print(f"Ingested {total_inserted + total_updated} nominations (inserted: {total_inserted}, updated: {total_updated})...")
                    elif status == "updated":
                        total_updated += 1
                        if (total_inserted + total_updated) % 100 == 0:
                            conn.commit()
                            print(f"Ingested {total_inserted + total_updated} nominations (inserted: {total_inserted}, updated: {total_updated})...")

            conn.commit()
            conn.close()
            print(f"\nALL DONE. Ingested successfully out of {total_rows} CSV rows. Total Inserted: {total_inserted}, Total Updated: {total_updated}.")
            break
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            print(f"Database connection error: {e}. Re-syncing caches and retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()
