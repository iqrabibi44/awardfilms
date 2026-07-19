import mysql.connector
conn = mysql.connector.connect(host='127.0.0.1', user='root', password='', database='awardfilms_db')
cur = conn.cursor()
cur.execute("INSERT IGNORE INTO ceremonies (slug, name) VALUES ('critics-choice-awards', 'Critics Choice Awards');")
conn.commit()
cur.close()
conn.close()
print("Successfully inserted critics-choice-awards ceremony.")
