"""
stats.py — Prints a summary of the database after the pipeline completes.
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from db import get_connection

def print_stats():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM ceremonies")
            ceremonies = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM editions")
            editions = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM categories")
            categories = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM films")
            films = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM persons")
            persons = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM nominations")
            nominations = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM nominations WHERE is_winner = TRUE")
            winners = cur.fetchone()[0]

            cur.execute("""
                SELECT c.name FROM ceremonies c
                LEFT JOIN editions e ON c.id = e.ceremony_id
                WHERE e.id IS NULL
            """)
            zero_data = [r[0] for r in cur.fetchall()]

            cur.execute("SELECT COUNT(*) FROM films WHERE poster_url IS NULL")
            missing_posters = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM persons WHERE photo_url IS NULL")
            missing_photos = cur.fetchone()[0]

            cur.execute("""
                SELECT c.name, COUNT(n.id) as count
                FROM ceremonies c
                JOIN editions e ON c.id = e.ceremony_id
                JOIN nominations n ON e.id = n.edition_id
                GROUP BY c.name
                ORDER BY count DESC LIMIT 5
            """)
            top_ceremonies = cur.fetchall()

            cur.execute("""
                SELECT f.title, COUNT(n.id) as wins
                FROM films f
                JOIN nominations n ON f.id = n.film_id
                WHERE n.is_winner = TRUE
                GROUP BY f.title
                ORDER BY wins DESC LIMIT 5
            """)
            top_films = cur.fetchall()

            print("\n===================================")
            print("PIPELINE SUMMARY STATS")
            print("===================================")
            print(f"Total ceremonies in DB: {ceremonies}")
            print(f"Total editions in DB: {editions}")
            print(f"Total categories in DB: {categories}")
            print(f"Total films in DB: {films}")
            print(f"Total persons in DB: {persons}")
            print(f"Total nominations in DB: {nominations}")
            print(f"Total winners (is_winner = true): {winners}")
            print("")
            print(f"Films missing poster_url (need TMDb): {missing_posters}")
            print(f"Persons missing photo_url (need TMDb): {missing_photos}")
            print("")
            
            if zero_data:
                print("[warn] Ceremonies with ZERO data:")
                for c in zero_data:
                    print(f"   - {c}")
            else:
                print("✓ All ceremonies have data.")
            
            print("\n[top] Top 5 Ceremonies by Nomination Count:")
            for i, (name, count) in enumerate(top_ceremonies, 1):
                print(f"   {i}. {name}: {count}")

            print("\n[top] Top 5 Films by Win Count:")
            for i, (title, wins) in enumerate(top_films, 1):
                print(f"   {i}. {title}: {wins}")
                
            print("===================================\n")

    finally:
        conn.close()

if __name__ == "__main__":
    print_stats()
