import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(".env.local")
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute("SELECT id, name, slug FROM ceremonies WHERE country='Germany' OR name ILIKE '%German%'")
rows = cur.fetchall()
for r in rows:
    print(r)
