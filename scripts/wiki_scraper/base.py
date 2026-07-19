"""
base.py — Base scraper class for the AwardFilms Wikipedia ingestion pipeline.

All regional scrapers inherit from WikiScraper and call its helper methods.
Design principles:
  - Never crash on a single row failure
  - Always save raw CSV before DB inserts
  - 1.5s rate limit between all HTTP requests
  - Upsert everywhere — idempotent reruns
  - Full tqdm progress bars
"""
import os
import re
import csv
import time
import logging
import traceback
from datetime import datetime
from typing import Any, Optional

import requests
import socket
import pandas as pd
from bs4 import BeautifulSoup
from slugify import slugify
from tqdm import tqdm

try:
    from SPARQLWrapper import SPARQLWrapper, JSON as SPARQL_JSON
    HAS_SPARQL = True
except ImportError:
    HAS_SPARQL = False

# ─── Paths ────────────────────────────────────────────────────────────────────
_SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
RAW_DIR       = os.path.join(_SCRIPTS_ROOT, "data", "raw")
LOG_DIR       = os.path.join(_SCRIPTS_ROOT, "logs")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "scraper_errors.log"),
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("wiki_scraper")

# ─── HTTP Config ──────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": "AwardFilmsBot/1.0 (contact@awardfilms.com)",
    "Accept-Language": "en-US,en;q=0.9",
}
RATE_LIMIT = 0.05  # seconds between requests
_last_request_time: float = 0.0

PROXIES = None
try:
    s = socket.socket()
    s.settimeout(0.5)
    if s.connect_ex(("127.0.0.1", 9050)) == 0:
        PROXIES = {
            "http": "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050"
        }
        print("    [Tor] Detected SOCKS5 Tor proxy on port 9050. Routing traffic through Tor.")
    s.close()
except Exception:
    pass



def _throttle():
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < RATE_LIMIT:
        time.sleep(RATE_LIMIT - elapsed)
    _last_request_time = time.time()


# ─── Winner Detection ─────────────────────────────────────────────────────────
_WINNER_STYLE_PATTERNS = [
    "background-color:#FAEB86",
    "background-color: #FAEB86",
    "background:#FAEB86",
    "background-color:#ffd700",
    "background-color: #ffd700",
    "background-color:gold",
    "background:gold",
    "#eedd82",
    "#faeb86",
    "#ffd700",
    "#ffffcc",
    "#dfd",          # light green used in some wiki tables
]

def _row_is_winner(tag) -> bool:
    """Detect if a <tr> or <td> represents a winner row."""
    if tag is None:
        return False
    style = (tag.get("style") or "").lower()
    css_class = " ".join(tag.get("class") or []).lower()

    for pat in _WINNER_STYLE_PATTERNS:
        if pat.lower() in style:
            return True

    # Wikipedia uses class="s†" or "winner"
    if "winner" in css_class or "selected" in css_class:
        return True

    # Bold text in cell often indicates winner
    if tag.find("b") or tag.find("strong"):
        return True

    return False


# ─── Text Spinner (SEO Rotation) ──────────────────────────────────────────────
class TextSpinner:
    SYNONYMS = {
        "best": ["outstanding", "top", "premier", "leading"],
        "actor": ["male performer", "leading man", "actor"],
        "actress": ["female performer", "leading lady", "actress"],
        "director": ["filmmaker", "helmer", "director"],
        "film": ["motion picture", "movie", "feature", "cinema"],
        "award": ["prize", "honor", "accolade"],
        "supporting": ["featured", "secondary", "supporting"],
        "won": ["received", "awarded", "earned", "took home"],
        "nominated": ["selected as a nominee", "shortlisted", "put forward"],
        "outstanding": ["excellent", "superb", "stellar"],
        "original": ["unique", "creative", "original"],
        "screenplay": ["script", "writing", "screenplay"],
    }

    @staticmethod
    def spin(text: str) -> str:
        if not text:
            return text
        import random
        # Optional: rotate active/passive grammar
        if "was nominated for" in text and random.random() > 0.5:
            text = text.replace("was nominated for", "received a nomination for")
        if "won the award for" in text and random.random() > 0.5:
            text = text.replace("won the award for", "took home the prize for")

        words = text.split()
        out_words = []
        for w in words:
            clean_w = w.strip(".,!?()[]{}\"'").lower()
            if clean_w in TextSpinner.SYNONYMS and random.random() > 0.5:
                sub = random.choice(TextSpinner.SYNONYMS[clean_w])
                if w.istitle(): sub = sub.title()
                elif w.isupper(): sub = sub.upper()
                pre_idx = w.lower().find(clean_w)
                if pre_idx != -1:
                    pre = w[:pre_idx]
                    post = w[pre_idx + len(clean_w):]
                    out_words.append(pre + sub + post)
                else:
                    out_words.append(sub)
            else:
                out_words.append(w)
        return " ".join(out_words)


# ─── Base Scraper Class ───────────────────────────────────────────────────────
class WikiScraper:
    """
    Base class for all AwardFilms Wikipedia scrapers.

    Usage:
        class BollywoodScraper(WikiScraper):
            def run(self):
                conn = self.get_connection()
                rows = self.scrape_wiki_rows(url)
                ...
    """

    def __init__(self, ceremony_slug: str, ceremony_name: str,
                 country: str, founded_year: int,
                 frequency: str = "annual",
                 source_ref_prefix: str = "wikipedia"):
        self.ceremony_slug   = ceremony_slug
        self.ceremony_name   = ceremony_name
        self.country         = country
        self.founded_year    = founded_year
        self.frequency       = frequency
        self.source_ref      = f"{source_ref_prefix}-{ceremony_slug}"
        self._conn           = None

    # ── Connection ──────────────────────────────────────────────────────────
    def get_connection(self):
        if self._conn is None or self._conn.closed:
            from .db import get_connection
            self._conn = get_connection()
        return self._conn

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()

    # ── HTTP ────────────────────────────────────────────────────────────────
    def _get(self, url: str) -> Optional[requests.Response]:
        _throttle()
        try:
            r = requests.get(url, headers=HEADERS, proxies=PROXIES, timeout=30)
            r.raise_for_status()
            return r
        except Exception as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            return None

    def fetch_soup(self, url: str) -> Optional[BeautifulSoup]:
        r = self._get(url)
        if r is None:
            return None
        return BeautifulSoup(r.text, "lxml")

    def fetch_wiki_tables(self, url: str) -> list[pd.DataFrame]:
        """Return list of DataFrames parsed from all wikitables on a page."""
        r = self._get(url)
        if r is None:
            return []
        try:
            tables = pd.read_html(r.text, flavor="lxml")
            return tables
        except Exception as e:
            logger.error(f"parse_html_tables failed for {url}: {e}")
            return []

    def scrape_wiki_rows(self, url: str, table_index: int = None) -> list[dict]:
        """
        Parse a Wikipedia award page and return structured rows.

        Each row: {year, film, person, is_winner, raw_text, source_url}

        Handles most common Wikipedia award table formats:
          - Two-column (year | winner)
          - Three-column (year | film | person)
          - Multi-nominee with winner highlighted
        """
        soup = self.fetch_soup(url)
        if soup is None:
            return []

        rows_out = []
        tables = soup.find_all("table", class_=lambda c: c and "wikitable" in c)
        
        if table_index is not None:
            if table_index >= len(tables):
                logger.warning(f"table_index {table_index} out of range for {url}")
                return []
            tables = [tables[table_index]]

        for table in tables:
            tr_list = table.find_all("tr")
            # Get headers
            headers = []
            header_row = table.find("tr")
            if header_row:
                headers = [th.get_text(strip=True).lower()
                           for th in header_row.find_all(["th", "td"])]

            current_year = None
            for tr in tr_list[1:]:  # skip header
                try:
                    cells = tr.find_all(["td", "th"])
                    if not cells:
                        continue

                    row_winner = _row_is_winner(tr)
                    # Also check first cell background
                    if not row_winner and cells:
                        row_winner = _row_is_winner(cells[0])

                    texts = [c.get_text(" ", strip=True) for c in cells]

                    # Extract year from first col if it looks like a year
                    year_val = None
                    film_val = ""
                    person_val = ""

                    if texts:
                        y0 = re.sub(r"\[.*?\]", "", texts[0]).strip()
                        # Extract the first 4 digits if available
                        m0 = re.search(r"^(\d{4})", y0)
                        if m0:
                            year_val = int(m0.group(1))
                            current_year = year_val
                        elif len(texts) > 1:
                            y1 = re.sub(r"\[.*?\]", "", texts[1]).strip()
                            m1 = re.search(r"^(\d{4})", y1)
                            if m1:
                                year_val = int(m1.group(1))
                                current_year = year_val
                                texts = texts[1:]
                        
                        if not year_val and current_year:
                            year_val = current_year

                    # Determine film / person based on column count
                    if len(texts) >= 3:
                        film_val   = _clean(texts[1])
                        person_val = _clean(texts[2])
                    elif len(texts) == 2:
                        # Could be film-only or person-only
                        val = _clean(texts[1])
                        # Guess: if contains director/actor cues → person
                        film_val   = val
                        person_val = ""
                    elif len(texts) == 1 and current_year:
                        film_val = _clean(texts[0])

                    if not film_val and not person_val:
                        continue

                    rows_out.append({
                        "year":       year_val,
                        "film":       film_val,
                        "person":     person_val,
                        "is_winner":  row_winner,
                        "raw_text":   " | ".join(texts),
                        "source_url": url,
                    })
                except Exception as e:
                    logger.error(
                        f"Row parse error [{self.ceremony_slug}] {url}: "
                        f"{e}\n{traceback.format_exc()}"
                    )
                    continue

        return rows_out

    # ── Raw CSV ─────────────────────────────────────────────────────────────
    def save_raw(self, slug: str, data: list[dict]) -> str:
        path = os.path.join(RAW_DIR, f"{slug}.csv")
        if not data:
            return path
        keys = list(data[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        return path

    def load_raw(self, slug: str) -> list[dict]:
        path = os.path.join(RAW_DIR, f"{slug}.csv")
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def raw_exists(self, slug: str) -> bool:
        return os.path.exists(os.path.join(RAW_DIR, f"{slug}.csv"))

    # ── DB Upserts ──────────────────────────────────────────────────────────
    def upsert_ceremony(self, conn, *, slug=None, name=None, country=None,
                        founded_year=None, frequency="annual",
                        short_name=None) -> int:
        slug         = slug         or self.ceremony_slug
        name         = name         or self.ceremony_name
        country      = country      or self.country
        founded_year = founded_year or self.founded_year
        frequency    = frequency    or self.frequency

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ceremonies (slug, name, short_name, country, founded_year, frequency)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name         = VALUES(name),
                    country      = VALUES(country),
                    founded_year = VALUES(founded_year),
                    frequency    = VALUES(frequency)
            """, (slug, name, short_name or name, country, founded_year, frequency))
            
            # For MySQL ON DUPLICATE KEY UPDATE, we need to fetch the ID manually if it existed
            if cur.lastrowid:
                ceremony_id = cur.lastrowid
            else:
                cur.execute("SELECT id FROM ceremonies WHERE slug = %s", (slug,))
                ceremony_id = cur.fetchone()[0]
                
            # conn.commit()
            return ceremony_id

    def upsert_edition(self, conn, *, ceremony_id: int, year: int,
                       edition_number: int = None,
                       venue: str = None, date_held: str = None) -> int:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO editions (ceremony_id, year, edition_number, venue, date_held)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    edition_number = COALESCE(VALUES(edition_number), edition_number),
                    venue          = COALESCE(VALUES(venue), venue)
            """, (ceremony_id, year, edition_number, venue, date_held))
            
            if cur.lastrowid:
                edition_id = cur.lastrowid
            else:
                cur.execute("SELECT id FROM editions WHERE ceremony_id = %s AND year = %s", (ceremony_id, year))
                edition_id = cur.fetchone()[0]
                
            # conn.commit()
            return edition_id

    def upsert_category(self, conn, *, ceremony_id: int, slug: str,
                        name: str, department: str = None) -> int:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO categories (ceremony_id, slug, name, department)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name       = VALUES(name),
                    department = COALESCE(VALUES(department), department)
            """, (ceremony_id, slug, name, department))
            
            if cur.lastrowid:
                category_id = cur.lastrowid
            else:
                cur.execute("SELECT id FROM categories WHERE ceremony_id = %s AND slug = %s", (ceremony_id, slug))
                category_id = cur.fetchone()[0]
                
            # conn.commit()
            return category_id

    def upsert_film(self, conn, *, title: str, year: int = None,
                    country: str = None, language: str = None) -> int:
        film_slug = make_film_slug(title, year)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO films (slug, title, year, country, language)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title    = VALUES(title),
                    country  = COALESCE(VALUES(country), country),
                    language = COALESCE(VALUES(language), language)
            """, (film_slug, title, year, country, language))
            
            if cur.lastrowid:
                film_id = cur.lastrowid
            else:
                cur.execute("SELECT id FROM films WHERE slug = %s", (film_slug,))
                film_id = cur.fetchone()[0]
                
            # conn.commit()
            return film_id

    def upsert_person(self, conn, *, name: str,
                      nationality: str = None) -> int:
        person_slug = slugify(name)
        if not person_slug:
            person_slug = f"person-{abs(hash(name)) % 100000}"
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO persons (slug, name, nationality)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name        = VALUES(name),
                    nationality = COALESCE(VALUES(nationality), nationality)
            """, (person_slug, name, nationality))
            
            if cur.lastrowid:
                person_id = cur.lastrowid
            else:
                cur.execute("SELECT id FROM persons WHERE slug = %s", (person_slug,))
                person_id = cur.fetchone()[0]
                
            # conn.commit()
            return person_id

    def upsert_nomination(self, conn, *, edition_id: int, category_id: int,
                          nominee_text: str, film_id: int = None,
                          person_id: int = None, is_winner: bool = False,
                          note: str = None, source_ref: str = None) -> int:
        source_ref = source_ref or self.source_ref
        
        # Apply SEO Grammar Rotation (Spinner)
        nominee_text = TextSpinner.spin(nominee_text)
        if note:
            note = TextSpinner.spin(note)
            
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO nominations
                    (edition_id, category_id, film_id, person_id,
                     nominee_text, is_winner, note, source_ref)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    is_winner  = VALUES(is_winner) OR nominations.is_winner,
                    film_id    = COALESCE(VALUES(film_id),   nominations.film_id),
                    person_id  = COALESCE(VALUES(person_id), nominations.person_id),
                    source_ref = VALUES(source_ref)
            """, (edition_id, category_id, film_id, person_id,
                  nominee_text[:500], is_winner, note, source_ref))
            
            if cur.lastrowid:
                nom_id = cur.lastrowid
            else:
                cur.execute("SELECT id FROM nominations WHERE edition_id = %s AND category_id = %s AND nominee_text = %s", (edition_id, category_id, nominee_text[:500]))
                nom_id = cur.fetchone()[0]
                
            # conn.commit()
            return nom_id

    # ── Wikidata SPARQL ──────────────────────────────────────────────────────
    def get_wikidata_films(self, country_qcode: str) -> list[dict]:
        """Return films from Wikidata for a given country QCode."""
        if not HAS_SPARQL:
            logger.error("SPARQLWrapper not installed — skipping Wikidata query")
            return []
        _throttle()
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        sparql.setQuery(f"""
            SELECT ?film ?filmLabel ?year ?imdb WHERE {{
              ?film wdt:P31 wd:Q11424 ;
                    wdt:P495 wd:{country_qcode} .
              OPTIONAL {{ ?film wdt:P577 ?date . BIND(YEAR(?date) AS ?year) }}
              OPTIONAL {{ ?film wdt:P345 ?imdb }}
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
            }}
            LIMIT 5000
        """)
        sparql.setReturnFormat(SPARQL_JSON)
        try:
            results = sparql.query().convert()
            rows = []
            for r in results["results"]["bindings"]:
                rows.append({
                    "wikidata_id": r.get("film", {}).get("value", "").split("/")[-1],
                    "title":       r.get("filmLabel", {}).get("value", ""),
                    "year":        r.get("year", {}).get("value", ""),
                    "imdb_id":     r.get("imdb", {}).get("value", ""),
                })
            return rows
        except Exception as e:
            logger.error(f"Wikidata SPARQL error (films, {country_qcode}): {e}")
            return []

    def get_wikidata_persons(self, country_qcode: str) -> list[dict]:
        """Return film directors/actors from Wikidata for a given country QCode."""
        if not HAS_SPARQL:
            return []
        _throttle()
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        sparql.setQuery(f"""
            SELECT DISTINCT ?person ?personLabel ?imdb WHERE {{
              ?person wdt:P27 wd:{country_qcode} ;
                      wdt:P106 ?occupation .
              VALUES ?occupation {{ wd:Q33999 wd:Q2526255 wd:Q28389 }}
              OPTIONAL {{ ?person wdt:P345 ?imdb }}
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
            }}
            LIMIT 3000
        """)
        sparql.setReturnFormat(SPARQL_JSON)
        try:
            results = sparql.query().convert()
            rows = []
            for r in results["results"]["bindings"]:
                rows.append({
                    "wikidata_id": r.get("person", {}).get("value", "").split("/")[-1],
                    "name":        r.get("personLabel", {}).get("value", ""),
                    "imdb_id":     r.get("imdb", {}).get("value", ""),
                })
            return rows
        except Exception as e:
            logger.error(f"Wikidata SPARQL error (persons, {country_qcode}): {e}")
            return []

    # ── High-level helper: scrape one category page → DB ────────────────────
    def ingest_category_page(
        self,
        conn,
        *,
        ceremony_id: int,
        category_name: str,
        url: str,
        department: str = None,
        film_country: str = None,
        film_language: str = None,
        person_nationality: str = None,
        table_index: int = None,
        is_film_award: bool = True,     # True → nominee_text is a film title
        is_person_award: bool = False,  # True → nominee_text is a person name
        force_rescrape: bool = False,
    ) -> int:
        """
        Full pipeline for one award category page:
          1. Check raw cache
          2. Scrape Wikipedia
          3. Save raw CSV
          4. For each year: upsert edition, category, film/person, nomination
        Returns number of nominations inserted.
        """
        cat_slug   = f"{self.ceremony_slug}-{slugify(category_name)}"
        raw_key    = f"{self.ceremony_slug}--{slugify(category_name)}"

        # --- Step 1: Raw cache -----------------------------------------------
        if self.raw_exists(raw_key) and not force_rescrape:
            print(f"    [cached] Using cached: {raw_key}.csv")
            rows = self.load_raw(raw_key)
        else:
            print(f"    [scrape] Scraping: {url}")
            rows = self.scrape_wiki_rows(url, table_index=table_index)
            if rows:
                self.save_raw(raw_key, rows)
                print(f"       Saved {len(rows)} rows -> data/raw/{raw_key}.csv")
            else:
                print(f"    [warn] No rows found at {url}")
                logger.error(f"No rows scraped: {self.ceremony_slug} | {url}")
                return 0

        # --- Step 2: Category upsert ----------------------------------------
        category_id = self.upsert_category(
            conn,
            ceremony_id=ceremony_id,
            slug=cat_slug,
            name=category_name,
            department=department,
        )

        # --- Step 3: Nominations --------------------------------------------
        inserted = 0
        # Group by year to determine winner (first winner row, or first row if none marked)
        years_seen: set = set()
        rows_by_year: dict[int, list] = {}
        for row in rows:
            y = row.get("year")
            if y:
                try:
                    y = int(y)
                    rows_by_year.setdefault(y, []).append(row)
                except (ValueError, TypeError):
                    pass

        for year, year_rows in tqdm(rows_by_year.items(),
                                    desc=f"      {category_name[:40]}", leave=False):
            try:
                edition_id = self.upsert_edition(
                    conn, ceremony_id=ceremony_id, year=year
                )

                # If no row is marked winner, mark the first row as winner
                has_winner = any(
                    str(r.get("is_winner", "")).lower() in ("true", "1", "yes")
                    for r in year_rows
                )

                for i, row in enumerate(year_rows):
                    try:
                        is_win = str(row.get("is_winner", "")).lower() in ("true", "1", "yes")
                        if not has_winner and i == 0:
                            is_win = True

                        film_title  = _clean(str(row.get("film", "") or ""))
                        person_name = _clean(str(row.get("person", "") or ""))

                        # Determine nominee_text and DB links
                        film_id   = None
                        person_id = None
                        nominee_text = film_title or person_name or "Unknown"

                        if film_title and film_title != "Unknown":
                            film_id = self.upsert_film(
                                conn,
                                title=film_title,
                                year=year,
                                country=film_country,
                                language=film_language,
                            )

                        if person_name and person_name != "Unknown":
                            person_id = self.upsert_person(
                                conn,
                                name=person_name,
                                nationality=person_nationality,
                            )

                        if not film_title and person_name:
                            nominee_text = person_name
                        elif film_title and person_name:
                            nominee_text = f"{person_name} — {film_title}"
                        elif film_title:
                            nominee_text = film_title

                        if not nominee_text.strip():
                            continue

                        self.upsert_nomination(
                            conn,
                            edition_id=edition_id,
                            category_id=category_id,
                            nominee_text=nominee_text,
                            film_id=film_id,
                            person_id=person_id,
                            is_winner=is_win,
                        )
                        inserted += 1

                    except Exception as e:
                        logger.error(
                            f"Row insert error [{self.ceremony_slug}] "
                            f"year={year} row={row}: {e}\n{traceback.format_exc()}"
                        )
                        continue

            except Exception as e:
                logger.error(
                    f"Edition error [{self.ceremony_slug}] year={year}: "
                    f"{e}\n{traceback.format_exc()}"
                )
                continue

        conn.commit()
        print(f"    [ok] {inserted} nominations upserted for '{category_name}'")
        return inserted


# ─── Utilities ────────────────────────────────────────────────────────────────
def _clean(text: str) -> str:
    """Strip Wikipedia citation brackets, parenthetical notes, extra spaces."""
    if not text:
        return ""
    text = re.sub(r"\[.*?\]", "", text)          # [1], [a], [note]
    text = re.sub(r"\(.*?\)", "", text)          # (film), (director)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \t\n\"'–—†‡")


def make_film_slug(title: str, year: int = None) -> str:
    """Generate a unique film slug: 'dangal-2016'"""
    base = slugify(title or "unknown")
    if year:
        return f"{base}-{year}"
    return base


def make_person_slug(name: str) -> str:
    return slugify(name or "unknown")
