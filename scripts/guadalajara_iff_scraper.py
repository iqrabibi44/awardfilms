"""
Guadalajara International Film Festival (FICG) - Dynamic Award Winners Scraper
Scrapes and parses complete categories and nominees from Wikipedia.
Output: guadalajara_iff_raw.csv
"""
import csv
import re
import os
from bs4 import BeautifulSoup

CEREMONY_NAME = "Guadalajara IFF Awards"
OUTPUT_FILE = "guadalajara_iff_raw.csv"
HTML_FILE = r"C:\Users\INFOTECH\.gemini\antigravity-ide\brain\25b9529c-cb08-4552-a6f2-edcd267c645b\.system_generated\steps\127\content.md"

def clean_text(text):
    if not text:
        return ""
    # Remove citation tags like [1]
    text = re.sub(r'\[.*?\]', '', text)
    # Remove parenthetical details
    text = re.sub(r'\(.*?\)', '', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip(" \t\n\r\"'–—†‡,.")

def main():
    if not os.path.exists(HTML_FILE):
        print(f"Error: HTML file not found at {HTML_FILE}")
        return

    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'lxml')
    parser_output = soup.find(class_='mw-parser-output')
    if not parser_output:
        parser_output = soup

    rows = []
    
    current_h2 = ""      # e.g., "Sección Largometraje Mexicano de Ficción"
    current_h3 = ""      # e.g., "Premios Mayahuel" or "Mejor película"
    
    # We walk through all elements in the parser output
    for element in parser_output.find_all(['h2', 'h3', 'h4', 'ul', 'div']):
        # If it's a div holding a heading (common in vector skin)
        if element.name == 'div' and 'mw-heading' in element.get('class', []):
            heading_tag = element.find(['h2', 'h3', 'h4'])
        elif element.name in ['h2', 'h3', 'h4']:
            heading_tag = element
        else:
            continue
            
        if not heading_tag:
            continue
            
        heading_text = clean_text(heading_tag.get_text())
        h_type = heading_tag.name
        
        if h_type == 'h2':
            current_h2 = heading_text
            current_h3 = ""
        elif h_type == 'h3':
            current_h3 = heading_text
            
        # For any heading h3 or h4, it could be a category.
        # Let's inspect next siblings to see if there is a ul with year list items.
        sibling = element.next_sibling
        while sibling:
            if sibling.name == 'ul':
                # Check if this ul contains year list items
                lis = sibling.find_all('li')
                has_year_items = False
                for li in lis:
                    if re.match(r'^(\d{4})[-–]?\d{0,4}:\s*', li.get_text().strip()):
                        has_year_items = True
                        break
                        
                if has_year_items:
                    # This heading is indeed a category!
                    # Determine full category name prefix
                    if h_type == 'h4':
                        category_name = heading_text
                        prefix = current_h3 or current_h2
                    else: # h3
                        category_name = heading_text
                        prefix = current_h2
                        
                    prefix = prefix.replace("Sección ", "").strip()
                    full_category = f"{prefix} - {category_name}" if prefix else category_name
                    
                    for li in lis:
                        li_text = li.get_text().strip()
                        match = re.match(r'^(\d{4})[-–]?\d{0,4}:\s*(.*)', li_text)
                        if match:
                            year = int(match.group(1))
                            rest = match.group(2).strip()
                            
                            film = ""
                            nominee = ""
                            
                            # Parse format e.g. "Film, de/por Director"
                            if ", de " in rest:
                                parts = rest.split(", de ", 1)
                                film = clean_text(parts[0])
                                nominee = clean_text(parts[1])
                            elif ", por " in rest:
                                parts = rest.split(", por ", 1)
                                nominee = clean_text(parts[0])
                                film = clean_text(parts[1])
                            elif " por " in rest:
                                parts = rest.split(" por ", 1)
                                nominee = clean_text(parts[0])
                                film = clean_text(parts[1])
                            else:
                                film = clean_text(rest)
                                nominee = clean_text(rest)
                                
                            if film or nominee:
                                rows.append({
                                    "year": year,
                                    "ceremony": CEREMONY_NAME,
                                    "category": full_category,
                                    "nominee": nominee or film,
                                    "film": film,
                                    "won": 1
                                })
                break
            elif sibling.name in ['h2', 'h3', 'h4'] or (sibling.name == 'div' and 'mw-heading' in sibling.get('class', [])):
                # Hit next heading, stop looking for ul
                break
            sibling = sibling.next_sibling

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["year", "ceremony", "category", "nominee", "film", "won"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} rows to {OUTPUT_FILE}")
    if rows:
        print(f"Years covered: {min(r['year'] for r in rows)} – {max(r['year'] for r in rows)}")

if __name__ == "__main__":
    main()
