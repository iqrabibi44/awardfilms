import pandas as pd
import os

csvs = {
    "FESPACO": "african_cinema/pan_african_cinema_awards/fespaco_etalon_dor/fespaco_awards.csv",
    "Carthage": "african_cinema/pan_african_cinema_awards/carthage_film_festival_awards/carthage_awards.csv",
    "ZIFF": "african_cinema/pan_african_cinema_awards/zanzibar_iff_awards/zanzibar_iff_awards.csv",
    "African Cinematography": "african_cinema/pan_african_cinema_awards/african_cinematography_awards/african_cinematography_awards.csv",
    "El Gouna": "african_cinema/pan_african_cinema_awards/el_gouna_film_festival_awards/el_gouna_awards.csv",
}

print("=== Pan-African Cinema Awards CSV Summary ===\n")
for name, path in csvs.items():
    if os.path.exists(path):
        df = pd.read_csv(path)
        years = sorted(df["year"].unique())
        print(f"{name}:")
        print(f"  Records: {len(df)}")
        print(f"  Years covered: {years}")
        print(f"  Sample:")
        print(df[["year","ceremony","category","nominee","film"]].head(3).to_string(index=False))
        print()
    else:
        print(f"{name}: FILE NOT FOUND at {path}\n")
