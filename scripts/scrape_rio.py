import requests
from bs4 import BeautifulSoup
import re
import csv

url = "https://pt.wikipedia.org/wiki/Lista_de_premiados_no_Festival_do_Rio"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}
r = requests.get(url, headers=headers)
if r.status_code != 200:
    print(f"Failed to fetch {url}, status: {r.status_code}")
    exit(1)
    
soup = BeautifulSoup(r.text, 'html.parser')
content_div = soup.find("div", id="mw-content-text")

h2s = content_div.find_all("h2")
parsed_rows = []

for h2 in h2s:
    year_text = re.sub(r"\[.*?\]", "", h2.get_text()).strip()
    if not year_text.isdigit() or len(year_text) != 4:
        continue
    year = int(year_text)
    
    sibling = h2.parent.next_sibling
    while sibling:
        if sibling.name:
            if sibling.get("class") and any("mw-heading" in cls for cls in sibling.get("class")):
                break
            if sibling.name == "section":
                sec_header = sibling.find(["h3", "h4"])
                sec_title = sec_header.get_text(strip=True).lower() if sec_header else ""
                if not sec_title:
                    sec_title = sibling.get_text(strip=True)[:100].lower()
                    
                is_official = "oficial" in sec_title or "premi" in sec_title
                if not is_official:
                    sibling = sibling.next_sibling
                    continue
                    
                for ul in sibling.find_all("ul"):
                    for li in ul.find_all("li"):
                        text = li.get_text(strip=True)
                        parts = re.split(r"\s*[\-—–:]\s*", text, 1)
                        if len(parts) < 2:
                            continue
                            
                        pt_cat = parts[0].strip()
                        details = parts[1].strip()
                        
                        cat_lower = pt_cat.lower()
                        eng_cat = None
                        if ("filme" in cat_lower or "longa-metragem" in cat_lower or "longa" in cat_lower or "longa metragem" in cat_lower) and "document" not in cat_lower and "curta" not in cat_lower:
                            eng_cat = "Best Film"
                        elif "diretor" in cat_lower or "direo" in cat_lower or "direção" in cat_lower:
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
                        
                        details_clean = re.sub(r"\[.*?\]", "", details).strip()
                        
                        if eng_cat == "Best Film":
                            if ", de " in details_clean:
                                f_part, d_part = details_clean.split(", de ", 1)
                                film = f_part.strip()
                                nominee = d_part.strip()
                            elif ", dirigido por " in details_clean:
                                f_part, d_part = details_clean.split(", dirigido por ", 1)
                                film = f_part.strip()
                                nominee = d_part.strip()
                            else:
                                film = details_clean
                        else:
                            if ", por " in details_clean:
                                n_part, f_part = details_clean.split(", por ", 1)
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
                            "ceremony": "Festival do Rio",
                            "category": eng_cat,
                            "nominee": nominee,
                            "film": film if film else nominee,
                            "won": 1
                        })
        sibling = sibling.next_sibling

# Save to CSV
output_path = r"c:\Users\INFOTECH\OneDrive\Desktop\Awardfilms\scripts\rio_raw.csv"
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["year", "ceremony", "category", "nominee", "film", "won"])
    writer.writeheader()
    writer.writerows(parsed_rows)

print(f"Scraped {len(parsed_rows)} rows and saved to {output_path}")
