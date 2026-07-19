import pandas as pd

CSV_PATH = "C:/Users/INFOTECH/OneDrive/Desktop/Awardfilms/lib/data/lollywood/hum-style-awards.csv"
df = pd.read_csv(CSV_PATH)

# Lines 236 to 251 have 2020, but these are actually for Parizaad, Raqeeb Se, Ehd-e-Wafa etc., which corresponds to the 8th Hum Awards held in 2022.
# Let's check which indices have year 2020 and change them to 2022.
df.loc[df['year'] == 2020, 'year'] = 2022

import csv
df.to_csv(CSV_PATH, index=False, quoting=csv.QUOTE_MINIMAL)
print("Updated hum-style-awards.csv years 2020 -> 2022")
