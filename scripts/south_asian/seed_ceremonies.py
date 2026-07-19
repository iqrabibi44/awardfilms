"""
scripts/south_asian/seed_ceremonies.py
Upserts Lollywood, Mollywood, and Sandalwood ceremonies into the DB (MySQL version).
"""
import os
import sys
import mysql.connector

CEREMONIES = [
    {
        "slug": "lux-style-awards",
        "name": "Lux Style Awards",
        "short_name": "LSA",
        "country": "Pakistan",
        "founded_year": 2002,
        "frequency": "annual",
        "description": "The Lux Style Awards are held annually in Pakistan to celebrate the style industry, acknowledging outstanding achievements in fashion, film, television, and music.",
    },
    {
        "slug": "ary-film-awards",
        "name": "ARY Film Awards",
        "short_name": "AFA",
        "country": "Pakistan",
        "founded_year": 2014,
        "frequency": "annual",
        "description": "The ARY Film Awards is an annual Pakistani film awards ceremony presented by ARY Digital Network to recognize excellence in the Pakistani film industry.",
    },
    {
        "slug": "hum-awards",
        "name": "Hum Awards",
        "short_name": "Hum",
        "country": "Pakistan",
        "founded_year": 2013,
        "frequency": "annual",
        "description": "The Hum Awards are held annually to recognize excellence in television, fashion, and music in Pakistan, with a dedicated section for Pakistani films.",
    },
    {
        "slug": "pisa",
        "name": "Pakistan International Screen Awards",
        "short_name": "PISA",
        "country": "Pakistan",
        "founded_year": 2019,
        "frequency": "annual",
        "description": "The Pakistan International Screen Awards honor exceptional talent across the film, television, and digital industries in Pakistan.",
    },
    {
        "slug": "nigar-awards",
        "name": "Nigar Awards",
        "short_name": "Nigar",
        "country": "Pakistan",
        "founded_year": 1957,
        "frequency": "annual",
        "description": "The Nigar Awards were the most prestigious film awards in Pakistan, established in 1957 by Nigar magazine to honor outstanding achievements in Pakistani cinema.",
    },
    {
        "slug": "kerala-state-film-awards",
        "name": "Kerala State Film Awards",
        "short_name": "Kerala State",
        "country": "India",
        "founded_year": 1969,
        "frequency": "annual",
        "description": "The Kerala State Film Awards are the film awards given for motion pictures made in the Malayalam language by the state government of Kerala, India.",
    },
    {
        "slug": "karnataka-state-film-awards",
        "name": "Karnataka State Film Awards",
        "short_name": "Karnataka State",
        "country": "India",
        "founded_year": 1967,
        "frequency": "annual",
        "description": "The Karnataka State Film Awards are the most notable film awards given for Kannada cinema, presented annually by the Government of Karnataka.",
    },
    {
        "slug": "asianet-film-awards",
        "name": "Asianet Film Awards",
        "short_name": "Asianet",
        "country": "India",
        "founded_year": 1998,
        "frequency": "annual",
        "description": "The Asianet Film Awards is an annual award ceremony for Malayalam films presented by Asianet, a Malayalam-language television network.",
    },
]

def get_db():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="",
        database="awardfilms_db",
        charset="utf8mb4",
        use_unicode=True,
        autocommit=True
    )

def seed(conn):
    cur = conn.cursor()
    try:
        for c in CEREMONIES:
            cur.execute(
                """
                INSERT INTO ceremonies
                    (slug, name, short_name, country, founded_year, frequency, description)
                VALUES (%(slug)s, %(name)s, %(short_name)s, %(country)s,
                        %(founded_year)s, %(frequency)s, %(description)s)
                ON DUPLICATE KEY UPDATE
                    name         = VALUES(name),
                    short_name   = VALUES(short_name),
                    country      = VALUES(country),
                    founded_year = VALUES(founded_year),
                    frequency    = VALUES(frequency),
                    description  = VALUES(description)
                """,
                c,
            )
            print(f"  [+]  {c['name']} seeded")
        conn.commit()
    finally:
        cur.close()
    print("\nAll South Asian ceremonies seeded.")

if __name__ == "__main__":
    print("Seeding Lollywood & South Asian ceremonies...")
    conn = get_db()
    seed(conn)
    conn.close()
