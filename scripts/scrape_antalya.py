import requests
from bs4 import BeautifulSoup
import re
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

headers_req = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

ORDINALS = {
    1:'1st',2:'2nd',3:'3rd',4:'4th',5:'5th',6:'6th',7:'7th',8:'8th',9:'9th',10:'10th',
    11:'11th',12:'12th',13:'13th',14:'14th',15:'15th',16:'16th',17:'17th',18:'18th',19:'19th',20:'20th',
    21:'21st',22:'22nd',23:'23rd',24:'24th',25:'25th',26:'26th',27:'27th',28:'28th',29:'29th',30:'30th',
    31:'31st',32:'32nd',33:'33rd',34:'34th',35:'35th',36:'36th',37:'37th',38:'38th',39:'39th',40:'40th',
    41:'41st',42:'42nd',43:'43rd',44:'44th',45:'45th',46:'46th',47:'47th',48:'48th',49:'49th',50:'50th',
    51:'51st',52:'52nd',53:'53rd',54:'54th',55:'55th',56:'56th',57:'57th',58:'58th',59:'59th',60:'60th',
    61:'61st',
}

FOCUS_CATS = {
    'best picture', 'best film', 'best feature film',
    'best director', 'best actress', 'best actor',
    'best supporting actor', 'best supporting actress',
    'best screenplay', 'best cinematography', 'best editing',
    'best music', 'best art direction',
}

def clean(text):
    text = re.sub(r'\[.*?\]', '', text)
    return ' '.join(text.split()).strip()

def edition_year(n):
    return 1963 + n

CATEGORY_MAP = {
    'best picture': 'Best Film',
    'best feature film': 'Best Film',
    'best film': 'Best Film',
    'best director': 'Best Director',
    'best actress': 'Best Actress',
    'best actor': 'Best Actor',
    'best supporting actor': 'Best Supporting Actor',
    'best supporting actress': 'Best Supporting Actress',
    'best screenplay': 'Best Screenplay',
    'best cinematography': 'Best Cinematography',
    'best editing': 'Best Editing',
    'best music': 'Best Music',
    'best art direction': 'Best Art Direction',
}

csv_rows = []
ceremony_name = "Antalya Golden Orange Film Awards"

for edition_num in range(1, 62):
    ord_str = ORDINALS[edition_num]
    url = f"https://en.wikipedia.org/wiki/{ord_str}_Antalya_Golden_Orange_Film_Festival"
    
    r = requests.get(url, headers=headers_req)
    if r.status_code != 200:
        continue
    
    year = edition_year(edition_num)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    tables = soup.find_all("table", class_=lambda c: c and "wikitable" in c)
    if not tables:
        continue
    
    edition_rows = 0
    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue
        
        header_row = rows[0]
        col_headers = [clean(th.get_text()).lower() for th in header_row.find_all(["th","td"])]
        
        if 'prize' not in col_headers and 'category' not in col_headers:
            continue
        
        for row in rows[1:]:
            cells = row.find_all(["td","th"])
            if len(cells) < 2:
                continue
            
            texts = [clean(c.get_text()) for c in cells]
            if not texts[0]:
                continue
            
            category_raw = texts[0].lower()
            if not any(cat in category_raw for cat in FOCUS_CATS):
                continue
            
            # Find category
            category = None
            for key, mapped in CATEGORY_MAP.items():
                if key in category_raw:
                    category = mapped
                    break
            if not category:
                continue
            
            # Parse film & nominee: Prize | (Prize$) | Film | Person
            film = ""
            nominee = ""
            
            if len(texts) >= 4:
                # Could be: Prize | Prize$ | Film | Person
                if re.match(r'^(TRY|₺|\$|USD)', texts[1]):
                    film = texts[2]
                    nominee = texts[3] if len(texts) > 3 else ""
                else:
                    film = texts[1]
                    nominee = texts[2]
            elif len(texts) == 3:
                film = texts[1]
                nominee = texts[2]
            elif len(texts) == 2:
                film = texts[1]
                nominee = ""
            
            # Skip if still money
            if re.match(r'^(TRY|₺|\$)', film):
                continue
            if not film:
                continue
            
            csv_rows.append({
                "year": year,
                "ceremony": ceremony_name,
                "category": category,
                "nominee": nominee,
                "film": film,
                "won": 1
            })
            edition_rows += 1
    
    print(f"Edition {edition_num} ({year}): {edition_rows} rows")

output_path = r"c:\Users\INFOTECH\OneDrive\Desktop\Awardfilms\scripts\antalya_raw.csv"
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["year","ceremony","category","nominee","film","won"])
    writer.writeheader()
    writer.writerows(csv_rows)

print(f"\nTotal rows: {len(csv_rows)}")
print(f"Saved to: {output_path}")
