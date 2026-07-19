"""
scripts/nollywood/db_stats_nollywood.py
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
            WHERE c.slug IN ('amaa', 'amvca', 'fespaco', 'nea', 'bona')
            GROUP BY c.slug
            ORDER BY noms DESC
            """
        )
        rows = cur.fetchall()
        print("\n=== Nollywood & African Cinema Pipeline Stats ===")
        for r in rows:
            print(f"{r[0]:<15} Editions: {r[1]:<5} Nominations: {r[2]}")
            
        cur.execute(
            """
            SELECT 
                COUNT(*) as total_films,
                SUM(CASE WHEN f.tmdb_id > 0 THEN 1 ELSE 0 END) as tmdb_matched,
                SUM(CASE WHEN f.tmdb_id = -1 THEN 1 ELSE 0 END) as tmdb_missing,
                SUM(CASE WHEN f.wikidata_id IS NOT NULL THEN 1 ELSE 0 END) as wikidata_matched
            FROM films f
            WHERE f.id IN (
                SELECT film_id FROM nominations n 
                JOIN editions e ON n.edition_id = e.id 
                JOIN ceremonies c ON e.ceremony_id = c.id 
                WHERE c.slug IN ('amaa', 'amvca', 'fespaco', 'nea', 'bona')
            )
            """
        )
        f_stats = cur.fetchone()
        print("\n=== Film Enrichment ===")
        print(f"Total African Films: {f_stats[0]}")
        print(f"TMDb Matched:        {f_stats[1]}")
        print(f"TMDb Missing (-1):   {f_stats[2]}")
        print(f"Wikidata Matched:    {f_stats[3]}")
    conn.close()

if __name__ == "__main__":
    main()
