"""
scripts/south_asian/eid_tracker.py
Eid Release Tracker
"""
import os
import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

def main():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    with conn.cursor() as cur:
        # Mock logic to demonstrate how we identify Eid releases by scanning known blockbuster titles.
        # In a full system, we would query release_date logic.
        cur.execute(
            """
            SELECT f.title, f.year, COUNT(n.id) as awards_won
            FROM films f
            JOIN nominations n ON n.film_id = f.id
            WHERE f.title IN (
                'Punjab Nahi Jaungi', 'Jawani Phir Nahi Ani', 'Waar', 
                'The Legend of Maula Jatt', 'London Nahi Jaunga', 'Bin Roye'
            ) AND n.is_winner = true
            GROUP BY f.title, f.year
            ORDER BY awards_won DESC
            """
        )
        results = cur.fetchall()
        print("\n=== Eid Blockbuster Release Tracker (Lollywood) ===")
        for r in results:
            print(f"{r[0]} ({r[1]}): {r[2]} Awards Won")
    conn.close()

if __name__ == "__main__":
    main()
