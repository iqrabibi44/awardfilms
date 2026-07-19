import os
import sys
import argparse
import time
import requests
import psycopg2
from dotenv import load_dotenv
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Load environment
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

def get_db_url():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set in environment.")
        sys.exit(1)
    return db_url

def get_tmdb_api_key():
    key = os.environ.get("TMDB_API_KEY")
    if not key:
        print("Error: TMDB_API_KEY not set in environment.")
        sys.exit(1)
    return key

def fuzzy_match(s1, s2):
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

def process_film(film_id, title, year, api_key, db_url):
    # Each thread must open its own database connection
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        session = requests.Session()
        
        # Clean title representing the film name
        search_url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": api_key,
            "query": title
        }
        if year:
            params["year"] = str(year)
            params["primary_release_year"] = str(year)

        # Search with year limit
        try:
            res = session.get(search_url, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            results = data.get("results", [])
        except Exception:
            results = []

        tmdb_movie = None
        if results:
            first_res = results[0]
            res_title = first_res.get("title", "")
            res_original_title = first_res.get("original_title", "")
            match_score = max(fuzzy_match(title, res_title), fuzzy_match(title, res_original_title))
            
            # Fallback search without year if year-restricted search had no results
            if match_score < 0.85 and year:
                params.pop("year", None)
                params.pop("primary_release_year", None)
                try:
                    res2 = session.get(search_url, params=params, timeout=10)
                    res2.raise_for_status()
                    results2 = res2.json().get("results", [])
                    if results2:
                        first_res2 = results2[0]
                        res_title2 = first_res2.get("title", "")
                        res_original_title2 = first_res2.get("original_title", "")
                        match_score2 = max(fuzzy_match(title, res_title2), fuzzy_match(title, res_original_title2))
                        if match_score2 >= 0.85:
                            first_res = first_res2
                            match_score = match_score2
                except Exception:
                    pass

            if match_score >= 0.85:
                tmdb_movie = first_res

        # If not found or not a valid movie, mark tmdb_id = -1
        if not tmdb_movie:
            with conn.cursor() as cur:
                cur.execute("UPDATE films SET tmdb_id = -1 WHERE id = %s", (film_id,))
            conn.commit()
            return film_id, False, "Not found on TMDb"

        # Fetch full movie details
        movie_id = tmdb_movie["id"]
        detail_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        detail_params = {"api_key": api_key}
        
        try:
            detail_res = session.get(detail_url, params=detail_params, timeout=10)
            detail_res.raise_for_status()
            details = detail_res.json()
        except Exception as e:
            return film_id, False, f"Detail API error for TMDb ID {movie_id}: {e}"

        # Extract enriched fields
        poster_path = details.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
        synopsis = details.get("overview")
        runtime = details.get("runtime")
        
        # Genre (comma-separated list of names)
        genres_list = details.get("genres", [])
        genre = ", ".join([g.get("name", "") for g in genres_list if g.get("name")]) if genres_list else None
        
        budget_usd = details.get("budget")
        budget_usd = int(budget_usd) if budget_usd else None
        
        box_office_usd = details.get("revenue")
        box_office_usd = int(box_office_usd) if box_office_usd else None
        
        imdb_id = details.get("imdb_id")
        lang = details.get("original_language")
        prod_countries = details.get("production_countries", [])
        country = prod_countries[0].get("name") if prod_countries else None

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE films
                SET poster_url = %s,
                    synopsis = %s,
                    runtime = %s,
                    genre = %s,
                    budget_usd = %s,
                    box_office_usd = %s,
                    imdb_id = %s,
                    tmdb_id = %s,
                    language = COALESCE(language, %s),
                    country = COALESCE(country, %s)
                WHERE id = %s
                """,
                (poster_url, synopsis, runtime, genre, budget_usd, box_office_usd, imdb_id, movie_id, lang, country, film_id)
            )
        conn.commit()
        return film_id, True, poster_url

    except Exception as e:
        return film_id, False, f"Exception: {e}"
    finally:
        if conn:
            conn.close()

def main():
    parser = argparse.ArgumentParser(description="Enrich films table with posters and metadata from TMDb concurrently")
    parser.add_argument("--limit", type=int, default=1000, help="Maximum number of films to process")
    parser.add_argument("--workers", type=int, default=15, help="Number of concurrent worker threads")
    args = parser.parse_args()

    api_key = get_tmdb_api_key()
    db_url = get_db_url()

    # Query all films to process in the main thread
    print("Connecting to database to fetch candidate films...")
    conn = psycopg2.connect(db_url)
    with conn.cursor() as cur:
        # We target films that have no poster AND haven't been searched yet (tmdb_id is NULL)
        cur.execute(
            """
            SELECT id, title, year
            FROM films
            WHERE (poster_url IS NULL OR poster_url = '') AND tmdb_id IS NULL
            ORDER BY year DESC
            LIMIT %s
            """,
            (args.limit,)
        )
        films = cur.fetchall()
    conn.close()

    if not films:
        print("No films need poster enrichment.")
        return

    print(f"Loaded {len(films)} films missing posters. Starting concurrent worker pool with {args.workers} threads...")

    success_count = 0
    failure_count = 0

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit tasks
        futures = {
            executor.submit(process_film, f[0], f[1], f[2], api_key, db_url): f
            for f in films
        }

        # Monitor progress with tqdm
        for future in tqdm(as_completed(futures), total=len(futures), desc="Fetching Posters"):
            film_info = futures[future]
            try:
                film_id, success, msg = future.result()
                if success:
                    success_count += 1
                else:
                    failure_count += 1
            except Exception as e:
                tqdm.write(f"Task for film {film_info[1]} ({film_info[2]}) generated an exception: {e}")

    print("\nEnrichment execution summary:")
    print(f"  Successfully found & updated: {success_count} films")
    print(f"  Unmatched / failed lookups (marked as -1): {failure_count} films")
    print("Finished poster enrichment!")

if __name__ == "__main__":
    main()
