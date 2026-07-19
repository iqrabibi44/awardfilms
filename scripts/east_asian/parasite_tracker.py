"""
scripts/east_asian/parasite_tracker.py
Dedicated script to track the 'Parasite Global Awards Journey' 
Outputs JSON summary of total ceremonies, wins, and win rate.
"""
import os
import sys
import json
import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

def get_db():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(url)

def main():
    conn = get_db()
    
    # We look for Parasite (2019) -> film slug usually 'parasite-2019' or similar.
    # To be safe, let's search by title 'Parasite' and year 2019.
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM films WHERE title ILIKE 'Parasite' AND year = 2019 LIMIT 1")
        row = cur.fetchone()
        
        if not row:
            print("Parasite (2019) not found in DB yet. Ensure Oscars/Baeksang pipelines have run.")
            sys.exit(0)
            
        film_id = row[0]
        
        cur.execute(
            """
            SELECT c.name as ceremony, c.country, n.is_winner 
            FROM nominations n
            JOIN editions e ON n.edition_id = e.id
            JOIN ceremonies c ON e.ceremony_id = c.id
            WHERE n.film_id = %s
            """,
            (film_id,)
        )
        nominations = cur.fetchall()

    conn.close()

    total_noms = len(nominations)
    total_wins = sum(1 for n in nominations if n[2])
    win_rate = (total_wins / total_noms * 100) if total_noms > 0 else 0
    
    unique_ceremonies = list(set(n[0] for n in nominations))
    
    data = {
        "film_title": "Parasite (2019)",
        "total_nominations_tracked": total_noms,
        "total_wins_tracked": total_wins,
        "win_rate_percentage": round(win_rate, 2),
        "total_ceremonies": len(unique_ceremonies),
        "ceremonies_list": unique_ceremonies
    }
    
    output_path = os.path.join(BASE_DIR, "data", "parasite_journey.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
        
    print(f"Parasite tracked! {total_wins} wins out of {total_noms} noms across {len(unique_ceremonies)} ceremonies.")
    print(f"Saved summary to {output_path}")

if __name__ == "__main__":
    main()
