import mysql.connector
conn = mysql.connector.connect(host='127.0.0.1', user='root', password='', database='awardfilms_db')
cur = conn.cursor()
cur.execute("INSERT IGNORE INTO ceremonies (slug, name) VALUES ('dga-awards', 'Directors Guild of America Awards');")
conn.commit()
cur.close()
conn.close()
print("Successfully inserted dga-awards ceremony.")
