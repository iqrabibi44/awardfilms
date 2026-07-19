import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1", port=3306, user="root", password="",
    database="awardfilms_db"
)
cur = conn.cursor(dictionary=True)

cur.execute("SELECT * FROM ceremonies WHERE name LIKE '%Iran%' OR name LIKE '%Cinema%'")
for r in cur.fetchall():
    print(r)
    
cur.close()
conn.close()
