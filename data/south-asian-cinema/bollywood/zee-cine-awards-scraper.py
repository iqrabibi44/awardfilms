import os
import pandas as pd
from wiki_scraper_utils import fetch_and_parse_wiki

FOUNDED_YEAR = 1998

CATEGORIES = [
    {"name": "Best Film", "canon": "BEST PICTURE", "wiki": "Zee_Cine_Award_for_Best_Film"},
    {"name": "Best Director", "canon": "DIRECTING", "wiki": "Zee_Cine_Award_for_Best_Director"},
    {"name": "Best Actor Male", "canon": "ACTOR IN A LEADING ROLE", "wiki": "Zee_Cine_Award_for_Best_Actor_-_Male"},
    {"name": "Best Actor Female", "canon": "ACTRESS IN A LEADING ROLE", "wiki": "Zee_Cine_Award_for_Best_Actor_-_Female"},
    {"name": "Best Supporting Actor", "canon": "ACTOR IN A SUPPORTING ROLE", "wiki": "Zee_Cine_Award_for_Best_Actor_in_a_Supporting_Role_-_Male"},
    {"name": "Best Supporting Actress", "canon": "ACTRESS IN A SUPPORTING ROLE", "wiki": "Zee_Cine_Award_for_Best_Actor_in_a_Supporting_Role_-_Female"},
]

def main():
    all_records = []
    for cat in CATEGORIES:
        print(f"Scraping {cat['name']}...")
        records = fetch_and_parse_wiki(cat['wiki'], cat['name'], cat['canon'], FOUNDED_YEAR)
        print(f"  Found {len(records)} records")
        all_records.extend(records)
        
    df = pd.DataFrame(all_records)
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    if not df.empty:
        cols = ['year_film', 'year_ceremony', 'ceremony', 'category', 'canon_category', 'name', 'film', 'winner']
        df = df[cols]
        df = df.drop_duplicates()
        output_file = os.path.join(output_dir, "zee_cine_awards.csv")
        df.to_csv(output_file, index=False, encoding="utf-8")
        print(f"Saved {len(df)} records to {output_file}")
    else:
        print("No records extracted.")

if __name__ == "__main__":
    main()
