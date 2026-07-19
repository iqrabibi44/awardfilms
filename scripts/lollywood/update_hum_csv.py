import pandas as pd

# Records to add to Hum Awards
records = []

# 9th Hum Awards (2024)
hum_9 = [
    # 2022 Awards
    ("Best Drama Serial", "Sang-e-Mah", ""),
    ("Best Director Drama Serial", "Saife Hassan", "Sang-e-Mah"),
    ("Best Writer Drama Serial", "Mustafa Afridi", "Sang-e-Mah"),
    ("Best Actor", "Bilal Abbas Khan", "Dobara"),
    ("Best Actress", "Yumna Zaidi", "Bakhtawar"),
    ("Best Onscreen Couple", "Ahad Raza Mir & Ramsha Khan", "Hum Tum"),
    # 2023 Awards
    ("Best Drama Serial", "Fairy Tale", ""),
    ("Best Director Drama Serial", "Shahid Shafaat", "Muhabbat Gumshuda Meri"),
    ("Best Writer Drama Serial", "Hashim Nadeem", "Jhok Sarkar"),
    ("Best Actor", "Khushhal Khan", "Muhabbat Gumshuda Meri"),
    ("Best Actress", "Mawra Hocane", "Neem"),
    ("Best Onscreen Couple", "Hamza Sohail & Sehar Khan", "Fairy Tale"),
    # Combined
    ("Best Actor in a Negative Role", "Syed Jibran", "Neem"),
    ("Most Impactful Character", "Sania Saeed", "Sang-e-Mah"),
    ("Best Supporting Actor", "Asif Raza Mir", "Jhok Sarkar"),
    ("Best Supporting Actress", "Samiya Mumtaz", "Sang-e-Mah"),
    ("Best Television Sensation Male", "Atif Aslam", "Sang-e-Mah"),
    ("Best Television Sensation Female", "Mamya Shahjaffar", "Jhok Sarkar"),
    ("Best Original Soundtrack Popular", "Sahir Ali Bagga", "Sang-e-Mah")
]

for cat, winner, film in hum_9:
    records.append({
        "award_show": "Hum Style Awards",
        "category": cat,
        "year": 2024,
        "winner": winner,
        "film": film,
        "notes": ""
    })

# 10th Hum Awards (2025)
hum_10 = [
    ("Best Actor Popular", "Bilal Abbas Khan", "Ishq Murshid"),
    ("Best Actress Popular", "Sajal Aly", "Zard Patton Ka Bunn"),
    ("Best Actor Jury", "Adnan Siddiqui", "Khushbo Mein Basay Khat"),
    ("Best Actress Jury", "Sajal Aly", "Zard Patton Ka Bunn"),
    ("Global Star Award", "Hania Aamir", ""),
    ("Best Drama Serial", "Zard Patton Ka Bunn", ""),
    ("Best Director Drama Serial", "Saife Hassan", "Zard Patton Ka Bunn")
]

for cat, winner, film in hum_10:
    records.append({
        "award_show": "Hum Style Awards",
        "category": cat,
        "year": 2025,
        "winner": winner,
        "film": film,
        "notes": ""
    })

CSV_PATH = "C:/Users/INFOTECH/OneDrive/Desktop/Awardfilms/lib/data/lollywood/hum-style-awards.csv"
df = pd.read_csv(CSV_PATH)

df_new = pd.DataFrame(records)
df_combined = pd.concat([df, df_new], ignore_index=True)
import csv
df_combined.to_csv(CSV_PATH, index=False, quoting=csv.QUOTE_MINIMAL)
print("Updated Hum Awards 2024 & 2025")
