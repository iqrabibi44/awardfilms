import os
import sys
import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

url = os.environ.get("DATABASE_URL")
conn = psycopg2.connect(url)
with conn.cursor() as cur:
    cur.execute("""
        SELECT c.slug, COUNT(n.id) as noms
        FROM ceremonies c
        LEFT JOIN editions e ON e.ceremony_id = c.id
        LEFT JOIN nominations n ON n.edition_id = e.id
        GROUP BY c.slug
        ORDER BY noms DESC
    """)
    rows = cur.fetchall()
    for r in rows:
        print(f"{r[0]:<30} {r[1]}")
conn.close()
