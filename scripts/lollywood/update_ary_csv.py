import pandas as pd

# Records to add to ARY Film Awards
records = []

# ARY 1st (2014)
ary_1 = [
    ("Best Film Jury", "Zinda Bhaag", ""),
    ("Best Director Jury", "Bilal Lashari", "Waar"),
    ("Best Actor Jury", "Humayun Saeed", "Main Hoon Shahid Afridi"),
    ("Best Actress Jury", "Amna Ilyas", "Zinda Bhaag"),
    ("Best Film Viewers Choice", "Waar", ""),
    ("Best Director Viewers Choice", "Bilal Lashari", "Waar"),
    ("Best Actor Viewers Choice", "Shaan Shahid", "Waar"),
    ("Best Actress Viewers Choice", "Ayesha Khan", "Waar"),
    ("Best Supporting Actor", "Hamza Ali Abbasi", "Waar"),
    ("Best Supporting Actress", "Misha Shafi", "Waar"),
    ("Best Star Debut Male", "Hamza Ali Abbasi", "Main Hoon Shahid Afridi"),
    ("Best Star Debut Female", "Ayesha Khan", "Waar"),
    ("Best Actor in a Comic Role", "Ismail Tara", "Main Hoon Shahid Afridi"),
    ("Best Actor in a Negative Role", "Shamoon Abbasi", "Waar"),
    ("Best Independent Film", "Lamha", ""),
    ("Best Original Music", "Shani and Kami", "Main Hoon Shahid Afridi"),
    ("Best Male Playback Singer", "Rahat Fateh Ali Khan", "Zinda Bhaag"),
    ("Best Female Playback Singer", "Abida Parveen", "Ishq Khuda"),
    ("Best Story", "Meenu Gaur and Farjad Nabi", "Zinda Bhaag"),
    ("Best Screenplay", "Osman Khalid Butt", "Siyaah"),
    ("Best Dialogue", "Vasay Chaudhry", "Main Hoon Shahid Afridi"),
    ("Best Action", "Hassan Waqas Rana", "Waar"),
    ("Best Background Score", "Sahir Ali Bagga", "Zinda Bhaag"),
    ("Best Cinematography", "Bilal Lashari", "Waar"),
    ("Best Makeup and Hairstyling", "Nabila", "Main Hoon Shahid Afridi"),
    ("Best Costume Design", "Sarah Gandapur", "Chambaili"),
    ("Best Special Effects", "Hassan Waqas Rana", "Waar"),
    ("Best Editing", "Bilal Lashari", "Waar"),
    ("Best Choreography", "Pappu Samrat", "Main Hoon Shahid Afridi")
]

for cat, winner, film in ary_1:
    records.append({
        "award_show": "ARY Film Awards",
        "category": cat,
        "year": 2014,
        "winner": winner,
        "film": film,
        "notes": ""
    })

# ARY 2nd (2016)
ary_2 = [
    ("Best Film Jury", "Jawani Phir Nahi Ani", ""),
    ("Best Director Jury", "Nadeem Baig", "Jawani Phir Nahi Ani"),
    ("Best Actor Jury", "Sarmad Sultan Khoosat", "Manto"),
    ("Best Actress Jury", "Sania Saeed", "Manto"),
    ("Best Film Viewers Choice", "Jawani Phir Nahi Ani", ""),
    ("Best Director Viewers Choice", "Nadeem Baig", "Jawani Phir Nahi Ani"),
    ("Best Actor Viewers Choice", "Humayun Saeed", "Jawani Phir Nahi Ani"),
    ("Best Actress Viewers Choice", "Sohai Ali Abro", "Jawani Phir Nahi Ani"),
    ("Best Supporting Actor", "Hamza Ali Abbasi", "Jawani Phir Nahi Ani"),
    ("Best Supporting Actress", "Ayesha Khan", "Jawani Phir Nahi Ani"),
    ("Best Star Debut Male", "Danish Taimoor", "Jalaibee"),
    ("Best Star Debut Female", "Ayesha Omer", "Karachi Se Lahore"),
    ("Best Actor in a Comic Role", "Ahmed Ali Butt", "Jawani Phir Nahi Ani"),
    ("Best Actor in a Negative Role", "Ayaz Samoo", "Moor"),
    ("Best Male Playback Singer", "Rahat Fateh Ali Khan", "Halla Gulla"),
    ("Best Female Playback Singer", "Sara Raza Khan", "Wrong No."),
    ("Best Background Score", "Strings", "Moor"),
    ("Best Original Music", "Shani Arshad", "Jawani Phir Nahi Ani"),
    ("Best Story", "Vasay Chaudhry", "Jawani Phir Nahi Ani"),
    ("Best Screenplay", "Vasay Chaudhry", "Jawani Phir Nahi Ani"),
    ("Best Dialogue", "Vasay Chaudhry", "Jawani Phir Nahi Ani"),
    ("Best Action", "Viktor Krav", "Jawani Phir Nahi Ani"),
    ("Best Cinematography", "Farhan Hafeez", "Moor"),
    ("Best Choreography", "Shabina Khan", "Jawani Phir Nahi Ani"),
    ("Best Makeup and Hairstyling", "Nabila", "Jawani Phir Nahi Ani"),
    ("Best Costume Design", "Jahanzeb Qamar and Nabila", "Jawani Phir Nahi Ani"),
    ("Best Film Editing", "Rizwan AQ", "Jawani Phir Nahi Ani"),
    ("Best Special Effects Visual", "Tahir Moosa", "Moor")
]

for cat, winner, film in ary_2:
    records.append({
        "award_show": "ARY Film Awards",
        "category": cat,
        "year": 2016,
        "winner": winner,
        "film": film,
        "notes": ""
    })

CSV_PATH = "C:/Users/INFOTECH/OneDrive/Desktop/Awardfilms/lib/data/lollywood/ary-film-awards.csv"
df = pd.read_csv(CSV_PATH)
# Remove all 2014 records which are wrong
df = df[df['year'] != 2014]

df_new = pd.DataFrame(records)
df_combined = pd.concat([df, df_new], ignore_index=True)
import csv
df_combined.to_csv(CSV_PATH, index=False, quoting=csv.QUOTE_MINIMAL)
print("Updated ARY Film Awards 2014 & 2016")
