import os
import pandas as pd
from wiki_scraper_utils import fetch_and_parse_wiki

FOUNDED_YEAR = 1954

CATEGORIES = [
    {"name": "Best Feature Film", "canon": "BEST PICTURE", "wiki": "National_Film_Award_for_Best_Feature_Film"},
    {"name": "Best Direction", "canon": "DIRECTING", "wiki": "National_Film_Award_for_Best_Direction"},
    {"name": "Best Actor", "canon": "ACTOR IN A LEADING ROLE", "wiki": "National_Film_Award_for_Best_Actor"},
    {"name": "Best Actress", "canon": "ACTRESS IN A LEADING ROLE", "wiki": "National_Film_Award_for_Best_Actress"},
    {"name": "Best Supporting Actor", "canon": "ACTOR IN A SUPPORTING ROLE", "wiki": "National_Film_Award_for_Best_Supporting_Actor"},
    {"name": "Best Supporting Actress", "canon": "ACTRESS IN A SUPPORTING ROLE", "wiki": "National_Film_Award_for_Best_Supporting_Actress"},
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
        output_file = os.path.join(output_dir, "national_awards.csv")
        df.to_csv(output_file, index=False, encoding="utf-8")
        print(f"Saved {len(df)} records to {output_file}")
    else:
        print("No records extracted.")

if __name__ == "__main__":
    main()
