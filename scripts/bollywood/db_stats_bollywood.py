"""
scripts/bollywood/db_stats_bollywood.py
Prints statistics about the Bollywood data ingestion.
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

def get_db():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(url)

def main():
    conn = get_db()
    with conn.cursor() as cur:
        # Filmfare stats
        cur.execute("SELECT id FROM ceremonies WHERE slug = 'filmfare'")
        filmfare_row = cur.fetchone()
        if filmfare_row:
            fid = filmfare_row[0]
            cur.execute("SELECT COUNT(*) FROM editions WHERE ceremony_id = %s", (fid,))
            ed_count = cur.fetchone()[0]
            cur.execute(
                """
                SELECT COUNT(*) FROM nominations n
                JOIN editions e ON n.edition_id = e.id
                WHERE e.ceremony_id = %s
                """,
                (fid,)
            )
            nom_count = cur.fetchone()[0]
            print(f"Filmfare Editions:    {ed_count}")
            print(f"Filmfare Nominations: {nom_count}")
        else:
            print("Filmfare not found in DB.")

        # Overall Bollywood stats
        cur.execute(
            """
            SELECT c.slug, COUNT(n.id) as noms
            FROM ceremonies c
            LEFT JOIN editions e ON e.ceremony_id = c.id
            LEFT JOIN nominations n ON n.edition_id = e.id
            WHERE c.slug IN ('filmfare', 'national-film-awards-india', 'iifa', 'screen-awards', 'zee-cine-awards')
            GROUP BY c.slug
            ORDER BY noms DESC
            """
        )
        print("\nNominations by Ceremony:")
        for row in cur.fetchall():
            print(f"  {row[0]:<30} {row[1]}")

        # Missing links
        cur.execute(
            """
            SELECT COUNT(*) FROM nominations n
            JOIN editions e ON n.edition_id = e.id
            JOIN ceremonies c ON e.ceremony_id = c.id
            WHERE c.slug IN ('filmfare', 'national-film-awards-india', 'iifa', 'screen-awards', 'zee-cine-awards')
              AND n.person_id IS NULL
            """
        )
        missing_persons = cur.fetchone()[0]
        print(f"\nBollywood Nominations missing person_id: {missing_persons}")

    conn.close()

if __name__ == "__main__":
    main()
