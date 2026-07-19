"""
British scraper — BAFTA, BIFA
"""
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from base import WikiScraper

def scrape_bafta(conn):
    s = WikiScraper("bafta", "BAFTA Film Awards", "United Kingdom", 1948)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best Film", "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Film", "Film"),
        ("Best Direction", "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Direction", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Actor_in_a_Leading_Role", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Actress_in_a_Leading_Role", "Acting"),
        ("Best Supporting Actor", "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Actor_in_a_Supporting_Role", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Actress_in_a_Supporting_Role", "Acting"),
        ("Best Film Not in the English Language", "https://en.wikipedia.org/wiki/BAFTA_Award_for_Best_Film_Not_in_the_English_Language", "Film"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="United Kingdom"
        )

def scrape_bifa(conn):
    s = WikiScraper("bifa", "British Independent Film Awards", "United Kingdom", 1998)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Best British Independent Film", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_British_Independent_Film", "Film"),
        ("Best Director", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Director", "Directing"),
        ("Best Actor", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Performance_by_an_Actor_in_a_British_Independent_Film", "Acting"),
        ("Best Actress", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Performance_by_an_Actress_in_a_British_Independent_Film", "Acting"),
        ("Best Supporting Actor", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Supporting_Actor", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Supporting_Actress", "Acting"),
        ("Best Screenplay", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Screenplay", "Writing"),
        ("Best Documentary", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Documentary", "Documentary"),
        ("Best International Independent Film", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_International_Independent_Film", "Film"),
        ("Best British Short Film", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_British_Short_Film", "Short Film"),
        ("Best Cinematography", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Cinematography", "Cinematography"),
        ("Best Editing", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Editing", "Editing"),
        ("Best Make-Up & Hair Design", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Make-Up_%26_Hair_Design", "Makeup"),
        ("Best Music", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Music", "Music"),
        ("Best Production Design", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Production_Design", "Art Direction"),
        ("Best Sound", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Sound", "Sound"),
        ("Best Effects", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Effects", "Visual Effects"),
        ("Best Costume Design", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Costume_Design", "Costume Design"),
        ("Best Casting", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Best_Casting", "Casting"),
        ("Breakthrough Performance", "https://en.wikipedia.org/wiki/British_Independent_Film_Award_for_Breakthrough_Performance", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="United Kingdom", film_language="English"
        )

def scrape_lfcc(conn):
    s = WikiScraper("lfcc-awards", "London Film Critics Circle", "United Kingdom", 1980)
    ceremony_id = s.upsert_ceremony(conn)

    categories = [
        ("Film of the Year", "https://en.wikipedia.org/wiki/London_Film_Critics%27_Circle_Award_for_Film_of_the_Year", "Film"),
        ("Foreign Language Film of the Year", "https://en.wikipedia.org/wiki/London_Film_Critics%27_Circle_Award_for_Foreign_Language_Film_of_the_Year", "Film"),
        ("Director of the Year", "https://en.wikipedia.org/wiki/London_Film_Critics%27_Circle_Award_for_Director_of_the_Year", "Directing"),
        ("Screenwriter of the Year", "https://en.wikipedia.org/wiki/London_Film_Critics%27_Circle_Award_for_Screenwriter_of_the_Year", "Writing"),
        ("Actor of the Year", "https://en.wikipedia.org/wiki/London_Film_Critics%27_Circle_Award_for_Actor_of_the_Year", "Acting"),
        ("Actress of the Year", "https://en.wikipedia.org/wiki/London_Film_Critics%27_Circle_Award_for_Actress_of_the_Year", "Acting"),
        ("Supporting Actor of the Year", "https://en.wikipedia.org/wiki/London_Film_Critics%27_Circle_Award_for_Supporting_Actor_of_the_Year", "Acting"),
        ("Supporting Actress of the Year", "https://en.wikipedia.org/wiki/London_Film_Critics%27_Circle_Award_for_Supporting_Actress_of_the_Year", "Acting"),
        ("British Film of the Year", "https://en.wikipedia.org/wiki/London_Film_Critics%27_Circle_Award_for_British_Film_of_the_Year", "Film"),
        ("Technical Achievement", "https://en.wikipedia.org/wiki/London_Film_Critics%27_Circle_Award_for_Technical_Achievement", "Technical"),
        ("British Actor of the Year", "https://en.wikipedia.org/wiki/London_Film_Critics%27_Circle_Award_for_British_Actor_of_the_Year", "Acting"),
        ("British Actress of the Year", "https://en.wikipedia.org/wiki/London_Film_Critics%27_Circle_Award_for_British_Actress_of_the_Year", "Acting"),
    ]

    print(f"\n[{s.ceremony_name}]")
    for name, url, dept in categories:
        s.ingest_category_page(
            conn, ceremony_id=ceremony_id, category_name=name, url=url,
            department=dept, film_country="United Kingdom", film_language="English"
        )


def scrape_evening_standard(conn):
    import re
    from bs4 import BeautifulSoup
    from slugify import slugify
    
    s = WikiScraper("evening-standard-awards", "Evening Standard British Film Awards", "United Kingdom", 1973)
    ceremony_id = s.upsert_ceremony(conn)
    
    url = "https://en.wikipedia.org/wiki/Evening_Standard_British_Film_Awards"
    print(f"\n[{s.ceremony_name}]")
    print(f"    [scrape] Scraping single page: {url}")
    
    soup = s.fetch_soup(url)
    if not soup:
        return
        
    inserted = 0
    headers = soup.find_all(['h2', 'h3'])
    for header in headers:
        text = header.get_text(strip=True)
        m = re.match(r"^(\d{4})\s+Winners", text)
        if not m:
            continue
        year = int(m.group(1))
        
        # In modern Wikipedia, the h2/h3 is wrapped in <div class="mw-heading">
        block = header
        if block.parent and block.parent.name == 'div' and 'mw-heading' in (block.parent.get('class') or []):
            block = block.parent
            
        ul = None
        nxt = block.next_sibling
        while nxt:
            if getattr(nxt, 'name', None) == 'ul':
                ul = nxt
                break
            # Stop if we hit another heading
            if getattr(nxt, 'name', None) in ['h2', 'h3', 'div']:
                # Wait, only break if the div is another heading
                if getattr(nxt, 'name', None) == 'div' and 'mw-heading' not in (nxt.get('class') or []):
                    nxt = nxt.next_sibling
                    continue
                break
            nxt = nxt.next_sibling
            
        if not ul:
            continue
            
        edition_id = s.upsert_edition(conn, ceremony_id=ceremony_id, year=year)
        
        for li in ul.find_all('li'):
            item_text = li.get_text(" ", strip=True)
            if ':' not in item_text:
                continue
                
            parts = item_text.split(':', 1)
            cat_name = parts[0].strip()
            rest = parts[1].strip()
            
            # Try to split by dash variations
            dash_match = re.split(r'\s+[-—–]\s+', rest, maxsplit=1)
            person_name = ""
            film_title = ""
            
            if len(dash_match) == 2:
                person_name = dash_match[0].strip()
                film_title = dash_match[1].strip()
            else:
                film_title = rest
                
            cat_slug = f"evening-standard-{slugify(cat_name)}"
            category_id = s.upsert_category(conn, ceremony_id=ceremony_id, slug=cat_slug, name=cat_name)
            
            film_id = None
            person_id = None
            if film_title:
                film_id = s.upsert_film(conn, title=film_title, year=year, country="United Kingdom", language="English")
            if person_name:
                person_id = s.upsert_person(conn, name=person_name)
                
            nominee_text = f"{person_name} — {film_title}".strip(" —") if person_name else film_title
            if not nominee_text:
                nominee_text = rest
                
            s.upsert_nomination(
                conn, 
                edition_id=edition_id, 
                category_id=category_id, 
                nominee_text=nominee_text, 
                film_id=film_id, 
                person_id=person_id, 
                is_winner=True
            )
            inserted += 1
            
    print(f"    [ok] {inserted} winners upserted from single page")


if __name__ == "__main__":
    from db import get_connection
    conn = get_connection()
    scrape_bafta(conn)
    scrape_bifa(conn)
    scrape_lfcc(conn)
    scrape_evening_standard(conn)
    conn.commit()
    conn.close()
