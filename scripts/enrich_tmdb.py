import os
import sys
import argparse
import time
import requests
import psycopg2
from dotenv import load_dotenv
from difflib import SequenceMatcher
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

def fuzzy_match(s1, s2):
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

def main():
    parser = argparse.ArgumentParser(description="Enrich films table with metadata from TMDb")
    parser.add_argument("--limit", type=int, default=200, help="Maximum number of films to process")
    args = parser.parse_args()

    api_key = get_tmdb_api_key()
    conn = get_db_connection()

    # Get films that haven't been enriched yet (tmdb_id is NULL)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, title, year
            FROM films
            WHERE tmdb_id IS NULL
            LIMIT %s
            """,
            (args.limit,)
        )
        films = cur.fetchall()

    if not films:
        print("No films to enrich.")
        return

    print(f"Found {len(films)} films to process.")

    session = requests.Session()

    for film_id, title, year in tqdm(films, desc="Enriching Films"):
        # TMDB rate limit sleep
        time.sleep(0.26)
        
        # Search movie
        search_url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": api_key,
            "query": title
        }
        if year:
            params["year"] = str(year)
            params["primary_release_year"] = str(year)

        try:
            res = session.get(search_url, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            results = data.get("results", [])
        except Exception as e:
            # Silently log error to console or skip
            tqdm.write(f"Search API error for '{title}': {e}")
            continue

        tmdb_movie = None
        if results:
            # Take the first result if the title fuzzy matches
            first_res = results[0]
            res_title = first_res.get("title", "")
            res_original_title = first_res.get("original_title", "")
            
            match_score = max(fuzzy_match(title, res_title), fuzzy_match(title, res_original_title))
            
            # Fallback search without year if year-restricted search had no results
            if match_score < 0.85 and year:
                # Try search without year
                time.sleep(0.26)
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

        if not tmdb_movie:
            # Mark film with tmdb_id = -1 to avoid retrying
            with conn.cursor() as cur:
                cur.execute("UPDATE films SET tmdb_id = -1 WHERE id = %s", (film_id,))
            conn.commit()
            continue

        # Fetch full movie details
        movie_id = tmdb_movie["id"]
        time.sleep(0.26)
        detail_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        detail_params = {
            "api_key": api_key
        }
        
        try:
            detail_res = session.get(detail_url, params=detail_params, timeout=10)
            detail_res.raise_for_status()
            details = detail_res.json()
        except Exception as e:
            tqdm.write(f"Detail API error for movie ID {movie_id} ('{title}'): {e}")
            continue

        # Extract enriched fields
        poster_path = details.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
        synopsis = details.get("overview")
        runtime = details.get("runtime")
        
        # Genre (comma-separated list of names)
        genres_list = details.get("genres", [])
        genre = ", ".join([g.get("name", "") for g in genres_list if g.get("name")]) if genres_list else None
        
        budget_usd = details.get("budget")
        # Ensure it fits in BIGINT or is truthy
        budget_usd = int(budget_usd) if budget_usd else None
        
        box_office_usd = details.get("revenue")
        box_office_usd = int(box_office_usd) if box_office_usd else None
        
        imdb_id = details.get("imdb_id")
        
        # Language & Country mapping (optional extra details)
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

    conn.close()
    print("Film enrichment complete!")

if __name__ == "__main__":
    main()
