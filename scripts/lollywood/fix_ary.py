import pandas as pd
import requests
from bs4 import BeautifulSoup
import os

ARY_CSV_PATH = "C:/Users/INFOTECH/OneDrive/Desktop/Awardfilms/lib/data/lollywood/ary-film-awards.csv"

def get_ary_data(url, year):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    data = []
    # Find all tables with class 'wikitable'
    tables = soup.find_all('table', class_='wikitable')
    
    for table in tables:
        rows = table.find_all('tr')
        # We assume the first row with th is not always category, sometimes category is in th and winners in td
        # Typically wikipedia award tables have: Category | Winner | Film OR Category | Winner
        # Actually it's often a table with two columns: left category, right category, which is tricky.
        # Let's write a generic scraper for Wikipedia awards tables.
        
        # A simple way for ARY:
        # ARY Film Awards usually have tables where each row has Category (th or td) and Winner (td)
        for row in rows:
            cols = row.find_all(['th', 'td'])
            if len(cols) >= 2:
                # In many cases, it's 2 columns per category (e.g., Best Actor | Best Actress)
                # We need to parse correctly based on the table structure
                pass
                
    return data

# Instead of complex scraping which might fail on custom tables, let's use pandas read_html
def parse_with_pandas(url, year, show_name):
    dfs = pd.read_html(url)
    records = []
    
    for df in dfs:
        # Check if it looks like an awards table
        if df.shape[1] == 2 and not df.empty:
            # Often Wikipedia award tables have two columns for two different categories
            # e.g. "Best Actor" "Best Actress"
            #         winner       winner
            # We will just parse anything that looks like an award
            pass
            
parse_with_pandas("https://en.wikipedia.org/wiki/1st_ARY_Film_Awards", 2014, "ARY Film Awards")
