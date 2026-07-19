"""
scripts/south_asian/db_stats_south_asian.py
"""
import os
import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

def main():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.slug, COUNT(DISTINCT e.id) as editions, COUNT(n.id) as noms
            FROM ceremonies c
            LEFT JOIN editions e ON e.ceremony_id = c.id
            LEFT JOIN nominations n ON n.edition_id = e.id
            WHERE c.slug IN (
                'lux-style-awards', 'ary-film-awards', 'hum-awards', 'pisa', 'nigar-awards',
                'kerala-state-film-awards', 'karnataka-state-film-awards', 'asianet-film-awards'
            )
            GROUP BY c.slug
            ORDER BY noms DESC
            """
        )
        rows = cur.fetchall()
        print("\n=== South Asian Cinema Pipeline Stats ===")
        for r in rows:
            print(f"{r[0]:<30} Editions: {r[1]:<5} Nominations: {r[2]}")
            
    conn.close()

if __name__ == "__main__":
    main()
