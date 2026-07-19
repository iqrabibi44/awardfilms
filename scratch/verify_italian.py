import pandas as pd
import os

csvs = {
    "David di Donatello": "hollywood/italian_cinema_awards/david_di_donatello_awards/david_awards.csv",
    "Nastri d'Argento": "hollywood/italian_cinema_awards/nastri_dargento_awards/nastri_awards.csv",
    "Venice Film Festival": "hollywood/italian_cinema_awards/venice_film_festival/venice_awards.csv"
}

print("=== Italian Cinema Awards CSV Summary ===\n")
total = 0
for name, path in csvs.items():
    if os.path.exists(path):
        df = pd.read_csv(path)
        years = sorted(df["year"].unique())
        total += len(df)
        print(f"{name}:")
        print(f"  Records: {len(df)}")
        print(f"  Years covered: {years[:3]}...{years[-3:]}")
        print(f"  Sample:")
        print(df[["year","ceremony","category","nominee","film"]].head(2).to_string(index=False))
        print()
    else:
        print(f"{name}: FILE NOT FOUND at {path}\n")

print(f"Total Records Extracted: {total}")
