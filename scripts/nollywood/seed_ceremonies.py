"""
scripts/nollywood/seed_ceremonies.py
Upserts the 5 core Nollywood & African cinema ceremonies into the DB.
Run this FIRST before any ingestion scripts.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

CEREMONIES = [
    {
        "slug": "amaa",
        "name": "African Movie Academy Awards",
        "short_name": "AMAA",
        "country": "Nigeria",
        "founded_year": 2005,
        "frequency": "annual",
        "description": "The Africa Movie Academy Awards (AMAA) are presented annually to recognise excellence among professionals working in, or non-African professionals who have contributed to, the African film industry.",
    },
    {
        "slug": "amvca",
        "name": "Africa Magic Viewers' Choice Awards",
        "short_name": "AMVCA",
        "country": "Pan-African",
        "founded_year": 2013,
        "frequency": "annual",
        "description": "The Africa Magic Viewers' Choice Awards (AMVCA) is an annual accolade presented by MultiChoice recognizing outstanding achievement in television and film.",
    },
    {
        "slug": "fespaco",
        "name": "FESPACO Pan-African Film Festival",
        "short_name": "FESPACO",
        "country": "Burkina Faso",
        "founded_year": 1969,
        "frequency": "biennial",
        "description": "The Panafrican Film and Television Festival of Ouagadougou (FESPACO) is the largest film festival in Africa, held biennially in Burkina Faso since 1969. Its top prize is the prestigious Étalon de Yennenga.",
    },
    {
        "slug": "nea",
        "name": "Nigeria Entertainment Awards",
        "short_name": "NEA",
        "country": "Nigeria",
        "founded_year": 2002,
        "frequency": "annual",
        "description": "The Nigeria Entertainment Awards (NEA) were established in New York City in January 2006. The awards recognize the contributions of African entertainers to the entertainment industry.",
    },
    {
        "slug": "bona",
        "name": "Best of Nollywood Awards",
        "short_name": "BON Awards",
        "country": "Nigeria",
        "founded_year": 2006,
        "frequency": "annual",
        "description": "The Best of Nollywood Awards (BON Awards) is an annual film event presented by Best of Nollywood Magazine honoring outstanding achievements in the Nigerian movie industry.",
    },
]

def get_db():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)
    return psycopg2.connect(url)

def seed(conn):
    with conn.cursor() as cur:
        for c in CEREMONIES:
            cur.execute(
                """
                INSERT INTO ceremonies
                    (slug, name, short_name, country, founded_year, frequency, description)
                VALUES (%(slug)s, %(name)s, %(short_name)s, %(country)s,
                        %(founded_year)s, %(frequency)s, %(description)s)
                ON CONFLICT (slug) DO UPDATE SET
                    name         = EXCLUDED.name,
                    short_name   = EXCLUDED.short_name,
                    country      = EXCLUDED.country,
                    founded_year = EXCLUDED.founded_year,
                    frequency    = EXCLUDED.frequency,
                    description  = EXCLUDED.description
                RETURNING id
                """,
                c,
            )
            cid = cur.fetchone()[0]
            print(f"  ✅  {c['name']}  (id={cid})")
        conn.commit()
    print("\nAll Nollywood & African ceremonies seeded.")

if __name__ == "__main__":
    print("Seeding Nollywood ceremonies...")
    conn = get_db()
    seed(conn)
    conn.close()
