import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='',
    database='awardfilms_db'
)
cur = conn.cursor(dictionary=True)

# Counts
cur.execute('SELECT COUNT(*) as cnt FROM ceremonies')
print("Ceremonies:", cur.fetchone()['cnt'])

cur.execute('SELECT COUNT(*) as cnt FROM editions')
print("Editions:", cur.fetchone()['cnt'])

cur.execute('SELECT COUNT(*) as cnt FROM categories')
print("Categories:", cur.fetchone()['cnt'])

cur.execute('SELECT COUNT(*) as cnt FROM films')
print("Films:", cur.fetchone()['cnt'])

cur.execute('SELECT COUNT(*) as cnt FROM persons')
print("Persons:", cur.fetchone()['cnt'])

cur.execute('SELECT COUNT(*) as cnt FROM nominations')
print("Nominations:", cur.fetchone()['cnt'])

# Sample film
cur.execute('SELECT title, year, slug FROM films LIMIT 5')
print("\nSample Films:")
for row in cur.fetchall():
    print(row)

# Sample nomination
cur.execute('SELECT nominee_text, is_winner FROM nominations LIMIT 5')
print("\nSample Nominations:")
for row in cur.fetchall():
    print(row)

conn.close()
