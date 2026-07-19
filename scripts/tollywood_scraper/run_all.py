"""
run_all.py
Runs every award-show scraper in sequence, then concatenates all output
CSVs into one master dataset: output/tollywood_awards_master.csv

Usage:
    pip install -r requirements.txt
    python run_all.py
"""

import os
import csv
import traceback
from common import SCHEMA, log

os.makedirs("output", exist_ok=True)

SCRAPER_MODULES = [
    # Tollywood (Telugu)
    "scrape_filmfare_south_telugu",
    "scrape_siima",
    "scrape_nandi",
    "scrape_cinemaa",
    "scrape_santosham",
    # Kollywood (Tamil)
    "scrape_vijay_awards",
    "scrape_siima_tamil",
    "scrape_sun_kudumbam",
    "scrape_ananda_vikatan",
    "scrape_tn_state_film_awards",
]


def run_module(mod_name):
    log.info("=" * 60)
    log.info("Running %s", mod_name)
    log.info("=" * 60)
    try:
        mod = __import__(mod_name)
        mod.scrape()  # each module's __main__ block isn't triggered via import,
                       # so we call scrape() directly and write CSVs ourselves below
    except Exception:  # noqa: BLE001
        log.error("Scraper %s crashed:\n%s", mod_name, traceback.format_exc())


def merge_outputs():
    master_path = "output/tollywood_awards_master.csv"
    files = [f for f in os.listdir("output") if f.endswith(".csv") and "gaps" not in f and "master" not in f]

    all_rows = []
    for fname in files:
        path = os.path.join("output", fname)
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                all_rows.append(row)

    with open(master_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(SCHEMA)
        w.writerows(all_rows)

    log.info("Master file written: %s (%d total rows from %d files)", master_path, len(all_rows), len(files))


def write_readme():
    import collections
    counts = collections.Counter()
    master_path = "output/tollywood_awards_master.csv"
    if not os.path.exists(master_path):
        return
    with open(master_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            counts[row["award_show"]] += 1

    lines = ["# Tollywood/Kollywood Awards Dataset — Run Summary\n"]
    for show, n in counts.items():
        lines.append(f"- **{show}**: {n} rows")
    lines.append("\nSee each `*_gaps.csv` file for categories/years that could not be scraped automatically.")
    lines.append("Review gaps manually and supplement from official award sites or news archives.")

    with open("output/README.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    # NOTE: each scrape_*.py module writes its own output CSVs when run directly
    # (via `if __name__ == "__main__"`). Here we import + call scrape() then
    # write CSVs explicitly so a single `python run_all.py` produces everything.

    import scrape_filmfare_south_telugu as m1
    import scrape_siima as m2
    import scrape_nandi as m3
    import scrape_cinemaa as m4
    import scrape_santosham as m5
    import scrape_vijay_awards as m6
    import scrape_siima_tamil as m7
    import scrape_sun_kudumbam as m8
    import scrape_ananda_vikatan as m9
    import scrape_tn_state_film_awards as m10
    from common import write_csv, write_gaps

    jobs = [
        (m1, "output/filmfare_south_telugu.csv", "output/filmfare_south_telugu_gaps.csv"),
        (m2, "output/siima_telugu.csv", "output/siima_telugu_gaps.csv"),
        (m3, "output/nandi_awards.csv", "output/nandi_awards_gaps.csv"),
        (m4, "output/cinemaa_awards.csv", "output/cinemaa_awards_gaps.csv"),
        (m5, "output/santosham_awards.csv", "output/santosham_awards_gaps.csv"),
        (m6, "output/vijay_awards.csv", "output/vijay_awards_gaps.csv"),
        (m7, "output/siima_tamil.csv", "output/siima_tamil_gaps.csv"),
        (m8, "output/sun_kudumbam_viridhugal.csv", "output/sun_kudumbam_viridhugal_gaps.csv"),
        (m9, "output/ananda_vikatan_cinema_awards.csv", "output/ananda_vikatan_cinema_awards_gaps.csv"),
        (m10, "output/tn_state_film_awards.csv", "output/tn_state_film_awards_gaps.csv"),
    ]

    for mod, out_csv, out_gaps in jobs:
        log.info("=" * 60)
        log.info("Running %s", mod.__name__)
        log.info("=" * 60)
        try:
            if mod.__name__ in ("scrape_siima", "scrape_siima_tamil"):
                cat_rows, cat_gaps = mod.scrape_categories()
                ed_rows, ed_gaps = mod.scrape_editions()
                rows, gaps = cat_rows + ed_rows, cat_gaps + ed_gaps
            else:
                rows, gaps = mod.scrape()
            write_csv(rows, out_csv)
            write_gaps(gaps, out_gaps)
        except Exception:  # noqa: BLE001
            log.error("Scraper %s crashed:\n%s", mod.__name__, traceback.format_exc())

    merge_outputs()
    write_readme()
    log.info("ALL DONE. See output/ folder.")
