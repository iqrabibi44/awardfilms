"""
scripts/east_asian/seed_ceremonies.py
Upserts Korean and East Asian ceremonies into the DB (MySQL version).
"""
import os
import sys
import mysql.connector

CEREMONIES = [
    {
        "slug": "baeksang",
        "name": "Baeksang Arts Awards",
        "short_name": "Baeksang",
        "country": "South Korea",
        "founded_year": 1965,
        "frequency": "annual",
        "description": "The Baeksang Arts Awards are an awards ceremony held annually by IS PLUS Corp. to recognise outstanding achievements in the South Korean entertainment industry.",
    },
    {
        "slug": "grand-bell",
        "name": "Grand Bell Awards (Daejong)",
        "short_name": "Grand Bell",
        "country": "South Korea",
        "founded_year": 1962,
        "frequency": "annual",
        "description": "The Grand Bell Awards, also known as the Daejong Film Awards, is an awards ceremony presented annually by the Motion Pictures Association of Korea for excellence in film in South Korea.",
    },
    {
        "slug": "blue-dragon",
        "name": "Blue Dragon Film Awards",
        "short_name": "Blue Dragon",
        "country": "South Korea",
        "founded_year": 1963,
        "frequency": "annual",
        "description": "The Blue Dragon Film Awards is an annual awards ceremony that is presented by Sports Chosun for excellence in film in South Korea.",
    },
    {
        "slug": "japan-academy-film-prize",
        "name": "Japan Academy Film Prize",
        "short_name": "Japan Academy",
        "country": "Japan",
        "founded_year": 1978,
        "frequency": "annual",
        "description": "The Japan Academy Film Prize, often called the Japan Academy Awards, is a series of awards given annually since 1978 by the Nippon Academy-Sho Association for excellence in Japanese film.",
    },
    {
        "slug": "golden-horse",
        "name": "Golden Horse Awards",
        "short_name": "Golden Horse",
        "country": "Taiwan",
        "founded_year": 1962,
        "frequency": "annual",
        "description": "The Golden Horse Awards are a film festival and awards ceremony held annually in Taiwan. They are one of the most prestigious and time-honored film awards in the world of Chinese-language cinema.",
    },
    {
        "slug": "hkfa",
        "name": "Hong Kong Film Awards",
        "short_name": "HKFA",
        "country": "Hong Kong",
        "founded_year": 1982,
        "frequency": "annual",
        "description": "The Hong Kong Film Awards (HKFA) is an annual film awards ceremony in Hong Kong. It is the most prestigious film award in Hong Kong and among the most respected in mainland China and Taiwan.",
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
    print("\nAll East Asian ceremonies seeded.")

if __name__ == "__main__":
    print("Seeding East Asian ceremonies...")
    conn = get_db()
    seed(conn)
    conn.close()
