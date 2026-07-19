"""
scripts/bollywood/seed_ceremonies.py
Upserts the core Bollywood ceremonies into local MySQL (XAMPP).
Run this FIRST before any ingestion scripts.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import mysql.connector


CEREMONIES = [
    {
        "slug": "filmfare",
        "name": "Filmfare Awards",
        "short_name": "Filmfare",
        "country": "India",
        "founded_year": 1954,
        "frequency": "annual",
        "description": (
            "The Filmfare Awards are one of the oldest and most prestigious film "
            "award ceremonies in India, presented annually by The Times Group. "
            "Often referred to as 'the Oscars of Bollywood', they have been "
            "honouring excellence in Hindi cinema since 1954."
        ),
    },
    {
        "slug": "national-film-awards-india",
        "name": "National Film Awards India",
        "short_name": "National Awards",
        "country": "India",
        "founded_year": 1954,
        "frequency": "annual",
        "description": (
            "The National Film Awards are the most prominent film awards in India, "
            "presented by the Directorate of Film Festivals on behalf of the "
            "Ministry of Information and Broadcasting. They recognise excellence "
            "in all Indian languages, not just Hindi."
        ),
    },
    {
        "slug": "iifa",
        "name": "IIFA Awards",
        "short_name": "IIFA",
        "country": "India",
        "founded_year": 2000,
        "frequency": "annual",
        "description": (
            "The International Indian Film Academy Awards (IIFA) are presented "
            "annually by the IIFA organisation to celebrate achievements in "
            "Bollywood cinema. The ceremony is held in a different international "
            "city each year, spreading Bollywood globally."
        ),
    },
    {
        "slug": "screen-awards",
        "name": "Screen Awards",
        "short_name": "Screen",
        "country": "India",
        "founded_year": 1994,
        "frequency": "annual",
        "description": (
            "The Screen Awards, presented by the Indian Express Group, are among "
            "the major annual Bollywood film awards ceremonies in India, "
            "recognising excellence in Hindi cinema since 1994."
        ),
    },
    {
        "slug": "zee-cine-awards",
        "name": "Zee Cine Awards",
        "short_name": "Zee Cine",
        "country": "India",
        "founded_year": 1998,
        "frequency": "annual",
        "description": (
            "The Zee Cine Awards are annual Bollywood film awards presented by "
            "Zee Entertainment Enterprises since 1998, one of India's leading "
            "media companies."
        ),
    },
    {
        "slug": "producers-guild",
        "name": "Producers Guild Film Awards",
        "short_name": "Producers Guild (Apsara)",
        "country": "India",
        "founded_year": 2004,
        "frequency": "annual",
        "description": (
            "The Producers Guild Film Awards (previously known as the Apsara Film & Television Producers Guild Awards) "
            "was an award instituted by the Film and Television Producers Guild of India to recognize excellence in Indian film and television."
        ),
    },
    {
        "slug": "stardust-awards",
        "name": "Stardust Awards",
        "short_name": "Stardust",
        "country": "India",
        "founded_year": 2004,
        "frequency": "annual",
        "description": (
            "The Stardust Awards were an annual Indian film award ceremony sponsored by Stardust magazine, "
            "recognising breakthrough performances and stars in Hindi cinema."
        ),
    },
]


def get_db():
    return mysql.connector.connect(
        host="127.0.0.1", port=3306, user="root", password="", database="awardfilms_db"
    )


def seed(conn):
    cur = conn.cursor()
    for c in CEREMONIES:
        cur.execute(
            """
            INSERT INTO ceremonies
                (slug, name, short_name, country, founded_year, frequency, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name         = VALUES(name),
                short_name   = VALUES(short_name),
                country      = VALUES(country),
                founded_year = VALUES(founded_year),
                frequency    = VALUES(frequency),
                description  = VALUES(description)
            """,
            (
                c["slug"], c["name"], c["short_name"], c["country"],
                c["founded_year"], c["frequency"], c["description"]
            ),
        )
        conn.commit()
        cur.execute("SELECT id FROM ceremonies WHERE slug = %s", (c["slug"],))
        cid = cur.fetchone()[0]
        print(f"  [+] {c['name']}  (id={cid})")
    cur.close()
    print("\n[+] All Bollywood ceremonies seeded.")


if __name__ == "__main__":
    print("Seeding Bollywood ceremonies...")
    conn = get_db()
    seed(conn)
    conn.close()
