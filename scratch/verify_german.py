import pandas as pd
import os

csvs = {
    "German Film Awards": "hollywood/german_cinema_awards/german_film_awards/lola_awards.csv",
    "Bavarian Film Awards": "hollywood/german_cinema_awards/bavarian_film_awards/bavarian_awards.csv",
    "Berlin IFF": "hollywood/german_cinema_awards/berlin_iff/berlin_awards.csv"
}

print("=== German Cinema Awards CSV Summary ===\n")
total = 0
for name, path in csvs.items():
    if os.path.exists(path):
        df = pd.read_csv(path)
        if len(df) == 0:
            print(f"{name}: 0 records\n")
            continue
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
