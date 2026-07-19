import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1", port=3306, user="root", password="",
    database="awardfilms_db"
)
cur = conn.cursor(dictionary=True)

cur.execute("SELECT id, name FROM categories WHERE name LIKE '%actor%'")
rows = cur.fetchall()
for r in rows:
    print(r)
    
cur.close()
conn.close()
