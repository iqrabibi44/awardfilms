#!/bin/bash
python scripts/ingest_oscars.py --csv scripts/data/the_oscar_award.csv
python scripts/enrich_tmdb.py --limit 500
python scripts/enrich_persons.py --limit 300
python scripts/db_stats.py
