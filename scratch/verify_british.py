import pandas as pd
import os

csvs = {
    "BAFTA": "hollywood/british_cinema_awards/bafta_film_awards/bafta_awards.csv",
    "BIFA": "hollywood/british_cinema_awards/bifa_awards/bifa_awards.csv",
    "London Critics": "hollywood/british_cinema_awards/london_film_critics_circle_awards/london_critics_awards.csv",
    "Evening Standard": "hollywood/british_cinema_awards/evening_standard_british_film_awards/evening_standard_awards.csv",
}

print("=== British Cinema Awards CSV Summary ===\n")
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
