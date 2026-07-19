import mysql.connector
conn = mysql.connector.connect(host='127.0.0.1', user='root', password='', database='awardfilms_db')
cur = conn.cursor()
cur.execute("UPDATE ceremonies SET slug='sag-awards' WHERE slug='screen-actors-guild-awards';")
conn.commit()
cur.close()
conn.close()
print("Successfully inserted ceremony.")
