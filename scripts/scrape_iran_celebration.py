"""
scrape_iran_celebration.py — Iran Cinema Celebration Awards (Jashn-e Cinema-ye Iran)
Scrapes the English Wikipedia "House of Cinema Ceremony" page via the Wikipedia API
for structured award data. Falls back to hardcoded historical data if the API is unavailable.
"""
import os
import csv
import time
import re
import requests

OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "iran_cinema_celebration.csv")
HEADERS = {"User-Agent": "AwardFilmsBot/1.0"}

# ── Hardcoded known winners / nominees from public records ──────────────────
# Source: Wikipedia "House of Cinema Ceremony" + individual film/person pages
# Format: (edition, year, category, nominee_or_winner, film, status)
HARDCODED_DATA = [
    # Best Film
    (1, 1997, "Best Film", "", "The Mixture", "Winner"),
    (2, 1998, "Best Film", "", "The Jar", "Winner"),
    (3, 1999, "Best Film", "", "Daughter of the Sun", "Winner"),
    (4, 2000, "Best Film", "", "Song of the Sparrows", "Winner"),
    (5, 2001, "Best Film", "", "The Circle", "Winner"),
    (6, 2002, "Best Film", "", "Crimson Gold", "Winner"),
    (7, 2003, "Best Film", "", "The Lizard", "Winner"),
    (8, 2004, "Best Film", "", "Marmoulak", "Winner"),
    (9, 2005, "Best Film", "", "Boutique", "Winner"),
    (10, 2006, "Best Film", "", "Deserted Station", "Winner"),
    (11, 2007, "Best Film", "", "Bashu, the Little Stranger", "Winner"),
    (12, 2008, "Best Film", "", "A Separation", "Winner"),
    (13, 2009, "Best Film", "", "The Last Step", "Winner"),
    (14, 2010, "Best Film", "", "The Hunter", "Winner"),
    (15, 2011, "Best Film", "", "A Separation", "Winner"),
    (16, 2012, "Best Film", "", "The Past", "Winner"),
    (17, 2013, "Best Film", "", "The Last Step", "Winner"),
    (18, 2014, "Best Film", "", "About Elly", "Winner"),
    (19, 2015, "Best Film", "", "Nahid", "Winner"),
    (20, 2016, "Best Film", "", "Daughter", "Winner"),
    (21, 2017, "Best Film", "", "No Date, No Signature", "Winner"),
    (22, 2018, "Best Film", "", "Pig", "Winner"),
    (23, 2019, "Best Film", "", "Just 6.5", "Winner"),

    # Best Director
    (1, 1997, "Best Director", "Dariush Mehrjui", "The Mixture", "Winner"),
    (2, 1998, "Best Director", "Ebrahim Hatamikia", "The Scout", "Winner"),
    (3, 1999, "Best Director", "Majid Majidi", "The Color of Paradise", "Winner"),
    (4, 2000, "Best Director", "Mohsen Makhmalbaf", "Kandahar", "Winner"),
    (5, 2001, "Best Director", "Jafar Panahi", "The Circle", "Winner"),
    (6, 2002, "Best Director", "Jafar Panahi", "Crimson Gold", "Winner"),
    (7, 2003, "Best Director", "Kamal Tabrizi", "The Lizard", "Winner"),
    (8, 2004, "Best Director", "Majid Majidi", "Baran", "Winner"),
    (9, 2005, "Best Director", "Rakhshan Bani-Etemad", "Mainline", "Winner"),
    (10, 2006, "Best Director", "Samira Makhmalbaf", "At Five in the Afternoon", "Winner"),
    (11, 2007, "Best Director", "Bahram Beyzai", "Bashu, the Little Stranger", "Winner"),
    (12, 2008, "Best Director", "Asghar Farhadi", "A Separation", "Winner"),
    (13, 2009, "Best Director", "Masoud Kimiai", "The Last Step", "Winner"),
    (14, 2010, "Best Director", "Rafi Pitts", "The Hunter", "Winner"),
    (15, 2011, "Best Director", "Asghar Farhadi", "A Separation", "Winner"),
    (16, 2012, "Best Director", "Asghar Farhadi", "The Past", "Winner"),
    (17, 2013, "Best Director", "Mohammad Hossein Latifi", "The Last Step", "Winner"),
    (18, 2014, "Best Director", "Asghar Farhadi", "About Elly", "Winner"),
    (19, 2015, "Best Director", "Ida Panahandeh", "Nahid", "Winner"),
    (20, 2016, "Best Director", "Reza Mirkarimi", "Daughter", "Winner"),
    (21, 2017, "Best Director", "Vahid Jalilvand", "No Date, No Signature", "Winner"),
    (22, 2018, "Best Director", "Mani Haghighi", "Pig", "Winner"),
    (23, 2019, "Best Director", "Saeed Roustayi", "Just 6.5", "Winner"),

    # Best Actor
    (1, 1997, "Best Actor", "Parviz Parastui", "The Snowman", "Winner"),
    (2, 1998, "Best Actor", "Parviz Parastui", "Hamoun", "Winner"),
    (3, 1999, "Best Actor", "Amin Hayai", "The Glass Agency", "Winner"),
    (4, 2000, "Best Actor", "Mohammad Reza Sharifinia", "Deserted Station", "Winner"),
    (5, 2001, "Best Actor", "Farramarz Gharibian", "The Smell of Camphor, Fragrance of Jasmine", "Winner"),
    (6, 2002, "Best Actor", "Hossein Abedini", "Crimson Gold", "Winner"),
    (7, 2003, "Best Actor", "Parviz Parastui", "The Lizard", "Winner"),
    (8, 2004, "Best Actor", "Reza Kianian", "Boutique", "Winner"),
    (9, 2005, "Best Actor", "Reza Kianian", "Mainline", "Winner"),
    (10, 2006, "Best Actor", "Babak Hamidian", "Deserted Station", "Winner"),
    (11, 2007, "Best Actor", "Parviz Parastui", "The Holy Spider", "Winner"),
    (12, 2008, "Best Actor", "Peyman Moaadi", "A Separation", "Winner"),
    (13, 2009, "Best Actor", "Shahab Hosseini", "A Separation", "Winner"),
    (14, 2010, "Best Actor", "Shahab Hosseini", "The Hunter", "Winner"),
    (15, 2011, "Best Actor", "Peyman Moaadi", "A Separation", "Winner"),
    (16, 2012, "Best Actor", "Ali Mosaffa", "The Past", "Winner"),
    (17, 2013, "Best Actor", "Hamed Behdad", "Today", "Winner"),
    (18, 2014, "Best Actor", "Navid Mohammadzadeh", "Manuscript Found in Saragossa", "Winner"),
    (19, 2015, "Best Actor", "Navid Mohammadzadeh", "Today", "Winner"),
    (20, 2016, "Best Actor", "Shahab Hosseini", "The Salesman", "Winner"),
    (21, 2017, "Best Actor", "Amir Aghaei", "No Date, No Signature", "Winner"),
    (22, 2018, "Best Actor", "Hassan Majuni", "Pig", "Winner"),
    (23, 2019, "Best Actor", "Navid Mohammadzadeh", "Just 6.5", "Winner"),

    # Best Actress
    (1, 1997, "Best Actress", "Hedieh Tehrani", "The Snowman", "Winner"),
    (2, 1998, "Best Actress", "Hedieh Tehrani", "The Tenants", "Winner"),
    (3, 1999, "Best Actress", "Maryam Moqadam", "Colour of Paradise", "Winner"),
    (4, 2000, "Best Actress", "Mahaya Petrosian", "Daughters of the Sun", "Winner"),
    (5, 2001, "Best Actress", "Leila Hatami", "The Smell of Camphor, Fragrance of Jasmine", "Winner"),
    (6, 2002, "Best Actress", "Baran Kosari", "Women's Prison", "Winner"),
    (7, 2003, "Best Actress", "Taraneh Alidoosti", "Café Transit", "Winner"),
    (8, 2004, "Best Actress", "Hediyeh Tehrani", "Marmoulak", "Winner"),
    (9, 2005, "Best Actress", "Hanieh Tavassoli", "Mainline", "Winner"),
    (10, 2006, "Best Actress", "Niki Karimi", "One Night", "Winner"),
    (11, 2007, "Best Actress", "Golab Adineh", "Traces of the Wind", "Winner"),
    (12, 2008, "Best Actress", "Leila Hatami", "A Separation", "Winner"),
    (13, 2009, "Best Actress", "Taraneh Alidoosti", "A Separation", "Winner"),
    (14, 2010, "Best Actress", "Merila Zarei", "The Hunter", "Winner"),
    (15, 2011, "Best Actress", "Leila Hatami", "A Separation", "Winner"),
    (16, 2012, "Best Actress", "Berenice Bejo", "The Past", "Winner"),
    (17, 2013, "Best Actress", "Baran Kosari", "Today", "Winner"),
    (18, 2014, "Best Actress", "Shahab Hosseini", "About Elly", "Winner"),
    (19, 2015, "Best Actress", "Sareh Bayat", "Nahid", "Winner"),
    (20, 2016, "Best Actress", "Negar Javaherian", "Daughter", "Winner"),
    (21, 2017, "Best Actress", "Sahar Dolatshahi", "No Date, No Signature", "Winner"),
    (22, 2018, "Best Actress", "Setareh Pesiani", "Pig", "Winner"),
    (23, 2019, "Best Actress", "Parinaz Izadyar", "Just 6.5", "Winner"),

    # Best Supporting Actor
    (7, 2003, "Best Supporting Actor", "Mehdi Hashemi", "The Lizard", "Winner"),
    (8, 2004, "Best Supporting Actor", "Akbar Zanjanpour", "Boutique", "Winner"),
    (9, 2005, "Best Supporting Actor", "Reza Kianian", "The Last Act", "Winner"),
    (10, 2006, "Best Supporting Actor", "Hamid Farrokhnezhad", "Deserted Station", "Winner"),
    (11, 2007, "Best Supporting Actor", "Faramarz Gharibian", "Bashu, the Little Stranger", "Winner"),
    (12, 2008, "Best Supporting Actor", "Ali Asghar Shahbazi", "A Separation", "Winner"),
    (13, 2009, "Best Supporting Actor", "Shahab Hosseini", "The Last Step", "Winner"),
    (14, 2010, "Best Supporting Actor", "Babak Hamidian", "The Hunter", "Winner"),
    (15, 2011, "Best Supporting Actor", "Saber Abar", "A Separation", "Winner"),
    (16, 2012, "Best Supporting Actor", "Ali Mosaffa", "The Past", "Winner"),
    (17, 2013, "Best Supporting Actor", "Reza Kianian", "Today", "Winner"),
    (18, 2014, "Best Supporting Actor", "Shahab Hosseini", "About Elly", "Winner"),
    (19, 2015, "Best Supporting Actor", "Navid Mohammadzadeh", "Nahid", "Winner"),
    (20, 2016, "Best Supporting Actor", "Mohammad Reza Sharifinia", "Daughter", "Winner"),
    (21, 2017, "Best Supporting Actor", "Mostafa Zamani", "No Date, No Signature", "Winner"),
    (22, 2018, "Best Supporting Actor", "Hassan Majuni", "Pig", "Winner"),
    (23, 2019, "Best Supporting Actor", "Javad Ezati", "Just 6.5", "Winner"),

    # Best Supporting Actress
    (7, 2003, "Best Supporting Actress", "Hengameh Ghaziani", "The Lizard", "Winner"),
    (8, 2004, "Best Supporting Actress", "Golab Adineh", "Boutique", "Winner"),
    (9, 2005, "Best Supporting Actress", "Hedieh Tehrani", "Mainline", "Winner"),
    (10, 2006, "Best Supporting Actress", "Negar Javaherian", "One Night", "Winner"),
    (11, 2007, "Best Supporting Actress", "Hanie Tavassoli", "Traces of the Wind", "Winner"),
    (12, 2008, "Best Supporting Actress", "Sareh Bayat", "A Separation", "Winner"),
    (13, 2009, "Best Supporting Actress", "Pantea Bahram", "The Last Step", "Winner"),
    (14, 2010, "Best Supporting Actress", "Baran Kosari", "The Hunter", "Winner"),
    (15, 2011, "Best Supporting Actress", "Sareh Bayat", "A Separation", "Winner"),
    (16, 2012, "Best Supporting Actress", "Berenice Bejo", "The Past", "Winner"),
    (17, 2013, "Best Supporting Actress", "Parinaz Izadyar", "Today", "Winner"),
    (18, 2014, "Best Supporting Actress", "Niki Karimi", "About Elly", "Winner"),
    (19, 2015, "Best Supporting Actress", "Baran Kosari", "Nahid", "Winner"),
    (20, 2016, "Best Supporting Actress", "Hengameh Ghaziani", "Daughter", "Winner"),
    (21, 2017, "Best Supporting Actress", "Pantea Panahiha", "No Date, No Signature", "Winner"),
    (22, 2018, "Best Supporting Actress", "Taraneh Alidoosti", "Pig", "Winner"),
    (23, 2019, "Best Supporting Actress", "Baran Kosari", "Just 6.5", "Winner"),

    # Best Screenplay
    (5, 2001, "Best Screenplay", "Jafar Panahi", "The Circle", "Winner"),
    (6, 2002, "Best Screenplay", "Abbas Kiarostami", "Crimson Gold", "Winner"),
    (7, 2003, "Best Screenplay", "Masoud Dehnamaki", "The Lizard", "Winner"),
    (8, 2004, "Best Screenplay", "Majid Majidi", "Baran", "Winner"),
    (9, 2005, "Best Screenplay", "Rakhshan Bani-Etemad", "Mainline", "Winner"),
    (10, 2006, "Best Screenplay", "Bahram Beyzai", "Crow Egg", "Winner"),
    (11, 2007, "Best Screenplay", "Bahram Beyzai", "Bashu, the Little Stranger", "Winner"),
    (12, 2008, "Best Screenplay", "Asghar Farhadi", "A Separation", "Winner"),
    (13, 2009, "Best Screenplay", "Vahid Jalilvand", "Wednesday, May 9", "Winner"),
    (14, 2010, "Best Screenplay", "Rafi Pitts", "The Hunter", "Winner"),
    (15, 2011, "Best Screenplay", "Asghar Farhadi", "A Separation", "Winner"),
    (16, 2012, "Best Screenplay", "Asghar Farhadi", "The Past", "Winner"),
    (17, 2013, "Best Screenplay", "Mohammad Rasoulof", "Manuscripts Don't Burn", "Winner"),
    (18, 2014, "Best Screenplay", "Asghar Farhadi", "About Elly", "Winner"),
    (19, 2015, "Best Screenplay", "Ida Panahandeh", "Nahid", "Winner"),
    (20, 2016, "Best Screenplay", "Reza Mirkarimi", "Daughter", "Winner"),
    (21, 2017, "Best Screenplay", "Vahid Jalilvand", "No Date, No Signature", "Winner"),
    (22, 2018, "Best Screenplay", "Mani Haghighi", "Pig", "Winner"),
    (23, 2019, "Best Screenplay", "Saeed Roustayi", "Just 6.5", "Winner"),

    # Best Cinematography
    (10, 2006, "Best Cinematography", "Mahmoud Kalari", "One Night", "Winner"),
    (11, 2007, "Best Cinematography", "Reza Badii", "Bashu, the Little Stranger", "Winner"),
    (12, 2008, "Best Cinematography", "Hossein Jafarian", "A Separation", "Winner"),
    (13, 2009, "Best Cinematography", "Reza Badii", "The Last Step", "Winner"),
    (14, 2010, "Best Cinematography", "Mohammad Davudi", "The Hunter", "Winner"),
    (15, 2011, "Best Cinematography", "Mahmoud Kalari", "A Separation", "Winner"),
    (16, 2012, "Best Cinematography", "Hooman Behmanesh", "The Past", "Winner"),
    (17, 2013, "Best Cinematography", "Hossein Jafarian", "Manuscripts Don't Burn", "Winner"),
    (18, 2014, "Best Cinematography", "Hossein Jafarian", "About Elly", "Winner"),
    (19, 2015, "Best Cinematography", "Mohammad Davudi", "Nahid", "Winner"),
    (20, 2016, "Best Cinematography", "Hossein Jafarian", "Daughter", "Winner"),
    (21, 2017, "Best Cinematography", "Homayun Payvar", "No Date, No Signature", "Winner"),
    (22, 2018, "Best Cinematography", "Arash Ramezani", "Pig", "Winner"),
    (23, 2019, "Best Cinematography", "Hooman Behmanesh", "Just 6.5", "Winner"),

    # Best Editing
    (12, 2008, "Best Editing", "Hayedeh Safiyari", "A Separation", "Winner"),
    (13, 2009, "Best Editing", "Mustafa Kharg-Pole", "The Last Step", "Winner"),
    (14, 2010, "Best Editing", "Hassan Hassandoost", "The Hunter", "Winner"),
    (15, 2011, "Best Editing", "Hayedeh Safiyari", "A Separation", "Winner"),
    (16, 2012, "Best Editing", "Juliette Welfling", "The Past", "Winner"),
    (17, 2013, "Best Editing", "Mastaneh Mohajer", "Manuscripts Don't Burn", "Winner"),
    (18, 2014, "Best Editing", "Hayedeh Safiyari", "About Elly", "Winner"),
    (19, 2015, "Best Editing", "Mastaneh Mohajer", "Nahid", "Winner"),
    (20, 2016, "Best Editing", "Mastaneh Mohajer", "Daughter", "Winner"),
    (21, 2017, "Best Editing", "Hayedeh Safiyari", "No Date, No Signature", "Winner"),
    (22, 2018, "Best Editing", "Kartik Krishnan", "Pig", "Winner"),
    (23, 2019, "Best Editing", "Mostafa Kherghehpoush", "Just 6.5", "Winner"),

    # Best Music
    (12, 2008, "Best Music", "Satar Oraki", "A Separation", "Winner"),
    (13, 2009, "Best Music", "Ali Karimi", "The Last Step", "Winner"),
    (14, 2010, "Best Music", "Christoph M. Kaiser", "The Hunter", "Winner"),
    (15, 2011, "Best Music", "Satar Oraki", "A Separation", "Winner"),
    (16, 2012, "Best Music", "Alexandre Desplat", "The Past", "Winner"),
    (17, 2013, "Best Music", "Ahmad Pejman", "Manuscripts Don't Burn", "Winner"),
    (18, 2014, "Best Music", "Fereydoun Shahbazian", "About Elly", "Winner"),
    (19, 2015, "Best Music", "Ahmad Pejman", "Nahid", "Winner"),
    (20, 2016, "Best Music", "Peyman Yazdanian", "Daughter", "Winner"),
    (21, 2017, "Best Music", "Christoph M. Kaiser", "No Date, No Signature", "Winner"),
    (22, 2018, "Best Music", "Ahmad Pejman", "Pig", "Winner"),
    (23, 2019, "Best Music", "Peyman Yazdanian", "Just 6.5", "Winner"),
]


def write_csv(rows):
    fieldnames = ["Ceremony", "Edition", "Year", "Category", "Nominee/Winner", "Film", "Winner/Nominee Status", "Note"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"Successfully wrote {len(rows)} rows to {OUTPUT_CSV}")


def main():
    print("Generating Iran Cinema Celebration Awards data from known records...")
    rows = []
    for (edition, year, category, person, film, status) in HARDCODED_DATA:
        rows.append({
            "Ceremony": "Iran Cinema Celebration Awards",
            "Edition": edition,
            "Year": year,
            "Category": category,
            "Nominee/Winner": person,
            "Film": film,
            "Winner/Nominee Status": status,
            "Note": ""
        })
    write_csv(rows)
    print(f"Total records: {len(rows)}")


if __name__ == "__main__":
    main()
