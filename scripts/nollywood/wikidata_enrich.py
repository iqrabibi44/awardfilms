"""
scripts/nollywood/wikidata_enrich.py
Queries Wikidata for Nollywood films missing wikidata_id.
"""
import os
import sys
import time
import psycopg2
from SPARQLWrapper import SPARQLWrapper, JSON
from dotenv import load_dotenv
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

def get_db():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def query_wikidata(title, year):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    # P31 = instance of, Q11424 = film
    # P495 = country of origin, Q1033 = Nigeria
    query = f"""
    SELECT ?film ?title ?year WHERE {{
      ?film wdt:P31 wd:Q11424 .
      ?film wdt:P495 wd:Q1033 .
      ?film rdfs:label ?title FILTER(lang(?title)='en')
      OPTIONAL {{ ?film wdt:P577 ?year }}
      FILTER(regex(?title, "^{title}$", "i"))
    }} LIMIT 5
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        bindings = results["results"]["bindings"]
        for b in bindings:
            w_id = b["film"]["value"].split("/")[-1]
            # If year provided, loosely verify if available
            if year and "year" in b:
                w_year = b["year"]["value"][:4]
                if abs(int(w_year) - year) <= 1:
                    return w_id
            else:
                return w_id # accept without year check if year is unknown or absent in wikidata
        return None
    except Exception as e:
        return None

def main():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT f.id, f.title, f.year
            FROM films f
            JOIN nominations n ON n.film_id = f.id
            JOIN editions e ON n.edition_id = e.id
            JOIN ceremonies c ON e.ceremony_id = c.id
            WHERE c.slug IN ('amaa', 'amvca', 'fespaco', 'nea', 'bona')
              AND f.wikidata_id IS NULL
            """
        )
        films = cur.fetchall()
        
    print(f"Found {len(films)} Nollywood/African films missing wikidata_id.")
    
    updates = 0
    with conn.cursor() as cur:
        for fid, title, year in tqdm(films, desc="Wikidata SPARQL"):
            wid = query_wikidata(title, year)
            if wid:
                cur.execute("UPDATE films SET wikidata_id = %s WHERE id = %s", (wid, fid))
                updates += 1
            time.sleep(1.0) # rate limit for wikidata
        conn.commit()
            
    conn.close()
    print(f"Wikidata enrichment: {updates} matched.")

if __name__ == "__main__":
    main()
