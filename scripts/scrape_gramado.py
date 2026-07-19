import requests
from bs4 import BeautifulSoup
import re
import csv

url = "https://pt.wikipedia.org/wiki/Lista_de_premiados_no_Festival_de_Gramado"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}
r = requests.get(url, headers=headers)
if r.status_code != 200:
    print(f"Failed to fetch {url}, status: {r.status_code}")
    exit(1)
    
soup = BeautifulSoup(r.text, 'html.parser')
content_div = soup.find("div", id="mw-content-text")
h2_wrappers = content_div.find_all("div", class_="mw-heading2")

parsed_rows = []

for w in h2_wrappers:
    year_text = re.sub(r"\[.*?\]", "", w.get_text()).strip()
    if not year_text.isdigit() or len(year_text) != 4:
        continue
        
    year = int(year_text)
    
    sibling = w.next_sibling
    while sibling:
        if sibling.name:
            if sibling.get("class") and any("mw-heading" in cls for cls in sibling.get("class")):
                break
            if sibling.name == "ul":
                for li in sibling.find_all("li"):
                    text = li.get_text(strip=True)
                    if text.startswith("Realizado") or ":" not in text:
                        continue
                        
                    parts = re.split(r":\s*", text, 1)
                    pt_cat = parts[0].strip()
                    details = parts[1].strip()
                    
                    cat_lower = pt_cat.lower()
                    eng_cat = None
                    if "filme" in cat_lower and "estrangeiro" not in cat_lower and "curta" not in cat_lower and "documentário" not in cat_lower:
                        if "ibero-americano" in cat_lower:
                            eng_cat = "Best Ibero-American Film"
                        else:
                            eng_cat = "Best Film"
                    elif "diretor" in cat_lower or "direção" in cat_lower:
                        eng_cat = "Best Director"
                    elif "ator" in cat_lower:
                        if "coadjuvante" in cat_lower:
                            eng_cat = "Best Supporting Actor"
                        else:
                            eng_cat = "Best Actor"
                    elif "atriz" in cat_lower:
                        if "coadjuvante" in cat_lower:
                            eng_cat = "Best Supporting Actress"
                        else:
                            eng_cat = "Best Actress"
                            
                    if not eng_cat:
                        continue
                        
                    nominee = ""
                    film = ""
                    
                    if eng_cat in ["Best Film", "Best Ibero-American Film"]:
                        film = re.sub(r"\[.*?\]", "", details).strip()
                    else:
                        details_clean = re.sub(r"\[.*?\]", "", details).strip()
                        # Handle "Nominee, por Film" or "Nominee por Film" or "Nominee (Film)"
                        if ", por " in details_clean:
                            n_part, f_part = details_clean.split(", por ", 1)
                            nominee = n_part.strip()
                            film = f_part.strip()
                        elif ", por" in details_clean:
                            n_part, f_part = details_clean.split(", por", 1)
                            nominee = n_part.strip()
                            film = f_part.strip()
                        elif " por " in details_clean:
                            n_part, f_part = details_clean.split(" por ", 1)
                            nominee = n_part.strip()
                            film = f_part.strip()
                        elif " (" in details_clean:
                            parts_paren = re.split(r"\s*\(", details_clean, 1)
                            nominee = parts_paren[0].strip()
                            film = parts_paren[1].rstrip(")").strip()
                        else:
                            nominee = details_clean
                            film = details_clean
                            
                    parsed_rows.append({
                        "year": year,
                        "ceremony": "Gramado Film Festival",
                        "category": eng_cat,
                        "nominee": nominee,
                        "film": film if film else nominee,
                        "won": 1
                    })
        sibling = sibling.next_sibling

# Save to CSV
output_path = r"c:\Users\INFOTECH\OneDrive\Desktop\Awardfilms\scripts\gramado_raw.csv"
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["year", "ceremony", "category", "nominee", "film", "won"])
    writer.writeheader()
    writer.writerows(parsed_rows)

print(f"Scraped {len(parsed_rows)} rows and saved to {output_path}")
