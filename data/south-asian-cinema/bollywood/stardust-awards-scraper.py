import os
import pandas as pd
from wiki_scraper_utils import fetch_and_parse_wiki

FOUNDED_YEAR = 2004

CATEGORIES = [
    {"name": "Superstar of the Year Male", "canon": "ACTOR IN A LEADING ROLE", "wiki": "Stardust_Award_for_Superstar_of_Tomorrow_-_Male"},
    {"name": "Superstar of the Year Female", "canon": "ACTRESS IN A LEADING ROLE", "wiki": "Stardust_Award_for_Superstar_of_Tomorrow_-_Female"},
    {"name": "Best Film", "canon": "BEST PICTURE", "wiki": "Stardust_Award_for_Best_Film"},
    {"name": "Best Director", "canon": "DIRECTING", "wiki": "Stardust_Award_for_Best_Director"},
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
        output_file = os.path.join(output_dir, "stardust_awards.csv")
        df.to_csv(output_file, index=False, encoding="utf-8")
        print(f"Saved {len(df)} records to {output_file}")
    else:
        print("No records extracted.")

if __name__ == "__main__":
    main()
