"""
run_all.py (Mollywood)
Runs every Mollywood award-show scraper, then concatenates outputs into
output/mollywood_awards_master.csv

This folder is self-contained and intentionally separate from the
Tollywood and Kollywood scraper folders - run independently.

Usage:
    pip install -r requirements.txt
    python run_all.py
"""

import os
import csv
import traceback
from common import SCHEMA, log

os.makedirs("output", exist_ok=True)


def merge_outputs():
    master_path = "output/mollywood_awards_master.csv"
    files = [f for f in os.listdir("output") if f.endswith(".csv") and "gaps" not in f and "master" not in f]

    all_rows = []
    for fname in files:
        path = os.path.join("output", fname)
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
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
    master_path = "output/mollywood_awards_master.csv"
    if not os.path.exists(master_path):
        return
    with open(master_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            counts[row["award_show"]] += 1

    lines = ["# Mollywood Awards Dataset — Run Summary\n"]
    for show, n in counts.items():
        lines.append(f"- **{show}**: {n} rows")
    lines.append("\nSee each `*_gaps.csv` file for categories/years that could not be scraped automatically.")
    lines.append("Review gaps manually and supplement from official award sites or news archives")
    lines.append("(Asianet, Vanitha magazine, Manorama, Mathrubhumi).")

    with open("output/README.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    import scrape_kerala_state_film_awards as m1
    import scrape_filmfare_south_malayalam as m2
    import scrape_asianet_film_awards as m3
    import scrape_vanitha_film_awards as m4
    import scrape_siima_malayalam as m5
    from common import write_csv, write_gaps

    jobs = [
        (m1, "output/kerala_state_film_awards.csv", "output/kerala_state_film_awards_gaps.csv"),
        (m2, "output/filmfare_south_malayalam.csv", "output/filmfare_south_malayalam_gaps.csv"),
        (m3, "output/asianet_film_awards.csv", "output/asianet_film_awards_gaps.csv"),
        (m4, "output/vanitha_film_awards.csv", "output/vanitha_film_awards_gaps.csv"),
        (m5, "output/siima_malayalam.csv", "output/siima_malayalam_gaps.csv"),
    ]

    for mod, out_csv, out_gaps in jobs:
        log.info("=" * 60)
        log.info("Running %s", mod.__name__)
        log.info("=" * 60)
        try:
            if mod.__name__ == "scrape_siima_malayalam":
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
