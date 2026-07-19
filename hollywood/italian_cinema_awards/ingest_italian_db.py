import os
import sys
import re
import pandas as pd
import mysql.connector
from mysql.connector import Error as MySQLError

# Add project root to sys.path so we can import lib.text_spinner
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))
from lib.text_spinner import TextParaphraser

# Use custom slugify if python-slugify isn't installed
try:
    from slugify import slugify
except ImportError:
    def slugify(t):
        import unicodedata
        t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
        return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", t.lower())).strip("-")

# ─── MySQL / XAMPP credentials ────────────────────────────────────────────────
MYSQL_CONFIG = {
    "host":       "127.0.0.1",
    "port":       3306,
    "user":       "root",
    "password":   "",
    "database":   "awardfilms_db",
    "charset":    "utf8mb4",
    "use_unicode": True,
    "autocommit": False,
}

CEREMONIES_CONFIG = {
    "david": {
        "slug": "david-di-donatello",
        "name": "David di Donatello Awards",
        "csv": "david_di_donatello_awards/david_awards.csv",
        "start_year": 1956,
        "country": "Italy",
        "language": "Italian"
    },
    "nastri": {
        "slug": "nastri-dargento",
        "name": "Nastri d'Argento Awards",
        "csv": "nastri_dargento_awards/nastri_awards.csv",
        "start_year": 1946,
        "country": "Italy",
        "language": "Italian"
    },
    "venice": {
        "slug": "venice-film-festival",
        "name": "Venice Film Festival",
        "csv": "venice_film_festival/venice_awards.csv",
        "start_year": 1932,
        "country": "Italy",
        "language": "Italian"
    }
}

DEPT_KEYWORDS = [
    ("direct",            "Directing",       True),
    ("actor",             "Acting",          True),
    ("actress",           "Acting",          True),
    ("screenplay",        "Writing",         True),
    ("writer",            "Writing",         True),
    ("writ",              "Writing",         True),
    ("cinematography",    "Camera",          True),
    ("cinematographer",   "Camera",          True),
    ("camera",            "Camera",          True),
    ("photography",       "Camera",          True),
    ("editing",           "Editing",         True),
    ("editor",            "Editing",         True),
    ("sound",             "Sound",           True),
    ("music",             "Music",           True),
    ("score",             "Music",           True),
    ("song",              "Music",           True),
    ("costume",           "Costume Design",  True),
    ("makeup",            "Other",           True),
    ("make-up",           "Other",           True),
    ("production design", "Art Direction",   True),
    ("art direction",     "Art Direction",   True),
    ("visual effect",     "Visual Effects",  True),
    ("special effect",    "Visual Effects",  True),
    ("animation",         "Film",            False),
    ("documentary",       "Documentary",     False),
    ("short film",        "Short Film",      False),
    ("short",             "Short Film",      False),
]


def clean_text(text):
    if not text or str(text).lower() in ("nan", "n/a", "none"):
        return ""
    text = re.sub(r'\[[^\]]+\]', '', str(text))
    text = text.replace('†', '').replace('*', '').replace('‡', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_department_and_craft(category_name):
    cat_lower = category_name.lower()
    for kw, dept, is_craft in DEPT_KEYWORDS:
        if kw in cat_lower:
            return dept, is_craft
    return "General", False


def get_db_connection():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except MySQLError as e:
        print(f"[-] ERROR: Could not connect to MySQL: {e}")
        sys.exit(1)


def ingest_ceremony(conn, config):
    paraphraser = TextParaphraser()
    slug       = config["slug"]
    name       = config["name"]
    csv_rel    = config["csv"]
    start_year = config["start_year"]
    country    = config["country"]
    language   = config.get("language", "Italian")

    italian_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(italian_dir, csv_rel)

    if not os.path.exists(csv_path):
        print(f"[-] Warning: CSV not found at {csv_path}. Skipping {name}.")
        return

    print(f"\n[*] Processing {name}...")
    df = pd.read_csv(csv_path)
    print(f"    Rows in CSV: {len(df)}")

    cur = conn.cursor()
    try:
        # ── Find or create ceremony ───────────────────────────────────────────
        cur.execute("SELECT id FROM ceremonies WHERE slug = %s", (slug,))
        row = cur.fetchone()
        if not row:
            cur.execute(
                "INSERT INTO ceremonies (name, slug, country) VALUES (%s, %s, %s)",
                (name, slug, country)
            )
            ceremony_id = cur.lastrowid
            print(f"    [+] Created ceremony '{name}' ID={ceremony_id}")
        else:
            ceremony_id = row[0]
            print(f"    [*] Found ceremony '{name}' ID={ceremony_id}")

        # Clear stale data
        cur.execute("DELETE FROM editions WHERE ceremony_id = %s",   (ceremony_id,))
        cur.execute("DELETE FROM categories WHERE ceremony_id = %s", (ceremony_id,))
        conn.commit()

        # ── Pass 1: Upsert categories ─────────────────────────────────────────
        unique_categories = df["category"].dropna().unique()
        category_id_map = {}
        for cat in unique_categories:
            cat = clean_text(cat)
            if not cat:
                continue
            cat_slug = f"{slug}-{slugify(cat)}"[:200]
            dept, is_craft = get_department_and_craft(cat)
            cur.execute(
                """
                INSERT INTO categories (ceremony_id, slug, name, department, is_craft)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE name = VALUES(name)
                """,
                (ceremony_id, cat_slug, cat, dept, int(is_craft))
            )
            cur.execute(
                "SELECT id FROM categories WHERE ceremony_id = %s AND slug = %s",
                (ceremony_id, cat_slug)
            )
            category_id_map[cat] = cur.fetchone()[0]
        conn.commit()
        print(f"    [+] Upserted {len(category_id_map)} categories.")

        # ── Pass 2: Upsert editions ───────────────────────────────────────────
        unique_years = df["year"].dropna().unique()
        edition_id_map = {}
        for year in unique_years:
            year = int(year)
            edition_num  = max(1, year - start_year + 1)
            edition_slug = f"{slug}-{year}"
            cur.execute(
                """
                INSERT INTO editions (ceremony_id, edition_number, year, slug)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE slug = VALUES(slug)
                """,
                (ceremony_id, edition_num, year, edition_slug)
            )
            cur.execute(
                "SELECT id FROM editions WHERE ceremony_id = %s AND year = %s",
                (ceremony_id, year)
            )
            edition_id_map[year] = cur.fetchone()[0]
        conn.commit()
        print(f"    [+] Upserted {len(edition_id_map)} editions.")

        # ── Pass 3: Upsert films ──────────────────────────────────────────────
        film_id_map = {}
        for _, row in df.iterrows():
            film_title = clean_text(row.get("film", ""))
            year       = int(row["year"])
            if not film_title or film_title.lower() in ("nan", "n/a"):
                continue
            film_key  = (film_title, year)
            if film_key in film_id_map:
                continue
            film_slug = slugify(f"{film_title} {year}")[:300]
            if not film_slug:
                continue
            cur.execute(
                """
                INSERT INTO films (slug, title, year, country, language)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE title = VALUES(title)
                """,
                (film_slug, film_title, year, country, language)
            )
            cur.execute("SELECT id FROM films WHERE slug = %s", (film_slug,))
            film_id_map[film_key] = cur.fetchone()[0]
        conn.commit()
        print(f"    [+] Upserted {len(film_id_map)} films.")

        # ── Pass 4: Batch-insert nominations ──────────────────────────────────
        nomination_rows = []
        for _, row in df.iterrows():
            year       = int(row["year"])
            cat        = clean_text(row.get("category", ""))
            nominee    = clean_text(row.get("nominee",  ""))
            film_title = clean_text(row.get("film",     ""))
            is_winner  = int(bool(row.get("winner", 0)))
            source_url = clean_text(row.get("source_url", ""))

            edition_id  = edition_id_map.get(year)
            category_id = category_id_map.get(cat)
            film_id     = film_id_map.get((film_title, year))

            if not edition_id or not category_id:
                continue

            nominee_str = (nominee or film_title or "Unknown")[:500]
            try:
                nominee_str = paraphraser.paraphrase(nominee_str)
            except Exception:
                pass
            source_ref  = (source_url[:200] if source_url else None)

            nomination_rows.append((
                edition_id, category_id, film_id, None,
                nominee_str, is_winner, source_ref
            ))

        if nomination_rows:
            cur.executemany(
                """
                INSERT IGNORE INTO nominations
                    (edition_id, category_id, film_id, person_id, nominee_text, is_winner, source_ref)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                nomination_rows
            )
        conn.commit()
        print(f"    [+] Inserted {len(nomination_rows)} nominations.")

    finally:
        cur.close()


def main():
    conn = get_db_connection()
    try:
        for ceremony_key, config in CEREMONIES_CONFIG.items():
            ingest_ceremony(conn, config)
        print("\n[+] All Italian cinema awards ingested successfully into MySQL!")
    except Exception as e:
        conn.rollback()
        print(f"\n[-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
