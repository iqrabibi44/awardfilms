import os
import sys
import argparse
import time
import requests
import psycopg2
from dotenv import load_dotenv
try:
    from slugify import slugify
except ImportError:
    import unicodedata
    import re
    def slugify(text):
        text = str(text)
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text).strip('-')
        return text
from tqdm import tqdm

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set in environment.")
        sys.exit(1)
    return psycopg2.connect(db_url)

def get_tmdb_api_key():
    key = os.environ.get("TMDB_API_KEY")
    if not key:
        print("Error: TMDB_API_KEY not set in environment.")
        sys.exit(1)
    return key

def clean_slug(conn, base_slug, tmdb_id):
    if tmdb_id != -1:
        with conn.cursor() as cur:
            cur.execute("SELECT slug FROM persons WHERE tmdb_id = %s", (tmdb_id,))
            row = cur.fetchone()
            if row:
                return row[0]

    slug = base_slug
    counter = 1
    while True:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM persons WHERE slug = %s", (slug,))
            if not cur.fetchone():
                return slug
        if tmdb_id != -1:
            slug = f"{base_slug}-{tmdb_id}"
            tmdb_id = -1
        else:
            slug = f"{base_slug}-{counter}"
            counter += 1

def main():
    parser = argparse.ArgumentParser(description="Enrich nominations with persons data from TMDb")
    parser.add_argument("--limit", type=int, default=300, help="Maximum number of nominee names to process")
    args = parser.parse_args()

    api_key = get_tmdb_api_key()
    conn = get_db_connection()

    # Get nominations where person_id is NULL and nominee_text is not a film title
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT nominee_text
            FROM nominations
            WHERE person_id IS NULL
              AND nominee_text NOT IN (SELECT title FROM films)
            LIMIT %s
            """,
            (args.limit,)
        )
        nominees = cur.fetchall()

    if not nominees:
        print("No nominee names to process.")
        conn.close()
        return

    print(f"Found {len(nominees)} unique nominee names to process.")

    session = requests.Session()

    for (nominee_text,) in tqdm(nominees, desc="Enriching Persons"):
        nominee_clean = nominee_text.strip()
        if not nominee_clean:
            continue

        # Rate limit sleep
        time.sleep(0.26)
        
        search_url = "https://api.themoviedb.org/3/search/person"
        params = {
            "api_key": api_key,
            "query": nominee_clean
        }

        try:
            res = session.get(search_url, params=params, timeout=10)
            res.raise_for_status()
            results = res.json().get("results", [])
        except Exception as e:
            tqdm.write(f"Search API error for '{nominee_clean}': {e}")
            continue

        tmdb_person = None
        if results:
            # Check the first result
            first_res = results[0]
            # Confident match if exact case-insensitive match or high popularity
            if first_res.get("name", "").lower() == nominee_clean.lower() or first_res.get("popularity", 0) > 1.0:
                tmdb_person = first_res

        if not tmdb_person:
            # Unmatched: insert placeholder person row to avoid reprocessing
            # Generate a unique slug for unmatched person
            base_slug = slugify(nominee_clean)
            if not base_slug:
                base_slug = "unnamed"
            slug = clean_slug(conn, f"{base_slug}-unmatched", -1)
            
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO persons (slug, name, tmdb_id)
                    VALUES (%s, %s, -1)
                    ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                    """,
                    (slug, nominee_clean)
                )
                person_id = cur.fetchone()[0]
                
                # Update nominations
                cur.execute(
                    "UPDATE nominations SET person_id = %s WHERE nominee_text = %s AND person_id IS NULL",
                    (person_id, nominee_text)
                )
            conn.commit()
            continue

        # Get full person details
        person_id_tmdb = tmdb_person["id"]
        time.sleep(0.26)
        detail_url = f"https://api.themoviedb.org/3/person/{person_id_tmdb}"
        detail_params = {
            "api_key": api_key,
            "append_to_response": "external_ids"
        }

        try:
            detail_res = session.get(detail_url, params=detail_params, timeout=10)
            detail_res.raise_for_status()
            details = detail_res.json()
        except Exception as e:
            tqdm.write(f"Detail API error for person ID {person_id_tmdb} ('{nominee_clean}'): {e}")
            continue

        name = details.get("name", nominee_clean)
        birthday = details.get("birthday")
        birth_year = None
        if birthday:
            parts = birthday.split("-")
            if parts and parts[0].isdigit():
                birth_year = int(parts[0])
        
        nationality = details.get("place_of_birth")
        biography = details.get("biography")
        
        profile_path = details.get("profile_path")
        photo_url = f"https://image.tmdb.org/t/p/w500{profile_path}" if profile_path else None
        
        external_ids = details.get("external_ids", {})
        imdb_id = external_ids.get("imdb_id")
        wikidata_id = external_ids.get("wikidata_id")

        base_slug = slugify(name)
        if not base_slug:
            base_slug = "unnamed"
        slug = clean_slug(conn, base_slug, person_id_tmdb)

        with conn.cursor() as cur:
            # Upsert into persons
            cur.execute(
                """
                INSERT INTO persons (slug, name, birth_year, nationality, biography, photo_url, imdb_id, tmdb_id, wikidata_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (slug)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    birth_year = COALESCE(persons.birth_year, EXCLUDED.birth_year),
                    nationality = COALESCE(persons.nationality, EXCLUDED.nationality),
                    biography = COALESCE(persons.biography, EXCLUDED.biography),
                    photo_url = COALESCE(persons.photo_url, EXCLUDED.photo_url),
                    imdb_id = COALESCE(persons.imdb_id, EXCLUDED.imdb_id),
                    tmdb_id = EXCLUDED.tmdb_id,
                    wikidata_id = COALESCE(persons.wikidata_id, EXCLUDED.wikidata_id)
                RETURNING id
                """,
                (slug, name, birth_year, nationality, biography, photo_url, imdb_id, person_id_tmdb, wikidata_id)
            )
            person_id_db = cur.fetchone()[0]

            # Update nominations for this nominee_text
            cur.execute(
                "UPDATE nominations SET person_id = %s WHERE nominee_text = %s AND person_id IS NULL",
                (person_id_db, nominee_text)
            )
        conn.commit()

    conn.close()
    print("Person enrichment complete!")

if __name__ == "__main__":
    main()
