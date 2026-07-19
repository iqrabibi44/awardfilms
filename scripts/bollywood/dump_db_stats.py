import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv('.env.local')
conn = psycopg2.connect(os.environ['DATABASE_URL'])

# Total missing stats
query_missing = """
SELECT c.name as ceremony, COUNT(*) as missing_records
FROM nominations n
JOIN editions e ON n.edition_id = e.id
JOIN ceremonies c ON e.ceremony_id = c.id
LEFT JOIN films f ON n.film_id = f.id
WHERE c.region = 'Bollywood'
AND (n.nominee_text IS NULL OR n.nominee_text = '' OR f.title IS NULL OR f.title = '' OR LENGTH(n.nominee_text) < 2)
GROUP BY c.name;
"""
df_missing = pd.read_sql(query_missing, conn)

# Get some samples
query = """
SELECT c.name as ceremony, e.year, cat.name as category, n.nominee_text, f.title as film_title, n.is_winner 
FROM nominations n
JOIN editions e ON n.edition_id = e.id
JOIN ceremonies c ON e.ceremony_id = c.id
JOIN categories cat ON n.category_id = cat.id
LEFT JOIN films f ON n.film_id = f.id
WHERE c.region = 'Bollywood'
AND (n.nominee_text IS NULL OR n.nominee_text = '' OR f.title IS NULL OR f.title = '' OR LENGTH(n.nominee_text) < 2)
LIMIT 50;
"""
df = pd.read_sql(query, conn)

with open('bollywood_db_stats.txt', 'w', encoding='utf-8') as f:
    f.write("Missing records by ceremony:\n")
    f.write(df_missing.to_string())
    f.write("\n\nSamples of messy records:\n")
    f.write(df.to_string())

conn.close()
print("Done")
