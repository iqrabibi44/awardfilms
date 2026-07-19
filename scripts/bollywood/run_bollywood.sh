#!/bin/bash
# scripts/bollywood/run_bollywood.sh

echo "Starting Bollywood Data Pipeline..."

# Ensure we're in the scripts directory or project root
# If running from project root, python paths will work as scripts/bollywood/...
# We will use python (or python3) assuming it's available.

PYTHON_CMD="python -X utf8"
if ! command -v python &> /dev/null; then
    PYTHON_CMD="python3 -X utf8"
fi

echo "1. Seeding Ceremonies..."
$PYTHON_CMD scripts/bollywood/seed_ceremonies.py

echo "2. Scraping Bollywood Data to CSVs..."
$PYTHON_CMD scripts/bollywood/scrape_filmfare.py
$PYTHON_CMD scripts/bollywood/scrape_iifa.py
$PYTHON_CMD scripts/bollywood/scrape_national.py
$PYTHON_CMD scripts/bollywood/scrape_screen.py
$PYTHON_CMD scripts/bollywood/scrape_stardust.py
$PYTHON_CMD scripts/bollywood/scrape_zee_cine.py
$PYTHON_CMD scripts/bollywood/scrape_producers_guild.py

echo "3. Ingesting Bollywood CSVs into DB..."
$PYTHON_CMD scripts/bollywood/ingest_bollywood_csvs.py

#echo "4. Enriching Bollywood Films from TMDb (Limit 500)..."
#$PYTHON_CMD scripts/bollywood/enrich_bollywood_tmdb.py --limit 500

#echo "5. Enriching Bollywood Persons from TMDb (Limit 300)..."
#$PYTHON_CMD scripts/bollywood/enrich_bollywood_persons.py --limit 300

echo "6. Generating Database Stats..."
$PYTHON_CMD scripts/bollywood/db_stats_bollywood.py

echo "Bollywood Pipeline Complete!"
