import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set in environment.")
        sys.exit(1)
    return psycopg2.connect(db_url)

def main():
    conn = get_db_connection()
    with conn.cursor() as cur:
        # Table counts
        tables = ["ceremonies", "editions", "categories", "films", "persons", "nominations"]
        print("=== DATABASE TABLE COUNTS ===")
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"{table:15} : {count}")
            
        print("\n=== SPECIFIC METRICS ===")
        
        # Nominations with is_winner = True
        cur.execute("SELECT COUNT(*) FROM nominations WHERE is_winner = True")
        winners = cur.fetchone()[0]
        print(f"{'Winners':15} : {winners}")

        # Films with poster_url NOT NULL
        cur.execute("SELECT COUNT(*) FROM films WHERE poster_url IS NOT NULL")
        films_with_posters = cur.fetchone()[0]
        print(f"{'Films w/ Poster':15} : {films_with_posters}")

        # Persons with photo_url NOT NULL
        cur.execute("SELECT COUNT(*) FROM persons WHERE photo_url IS NOT NULL")
        persons_with_photos = cur.fetchone()[0]
        print(f"{'Persons w/ Photo':15} : {persons_with_photos}")

        # Nominations with film_id IS NULL
        cur.execute("SELECT COUNT(*) FROM nominations WHERE film_id IS NULL")
        noms_no_film = cur.fetchone()[0]
        print(f"{'Noms w/o Film':15} : {noms_no_film}")

        # Nominations with person_id IS NULL
        cur.execute("SELECT COUNT(*) FROM nominations WHERE person_id IS NULL")
        noms_no_person = cur.fetchone()[0]
        print(f"{'Noms w/o Person':15} : {noms_no_person}")
        
    conn.close()

if __name__ == "__main__":
    main()
