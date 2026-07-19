#!/bin/bash
# scripts/east_asian/run_east_asian.sh

echo "Starting Korean & East Asian Cinema Pipeline..."

PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo "1. Seeding Ceremonies..."
$PYTHON_CMD scripts/east_asian/seed_ceremonies.py

echo "2. Ingesting Baeksang Arts Awards..."
$PYTHON_CMD scripts/east_asian/ingest_baeksang.py

echo "3. Ingesting Grand Bell Awards..."
$PYTHON_CMD scripts/east_asian/ingest_grand_bell.py

echo "4. Ingesting Blue Dragon Film Awards..."
$PYTHON_CMD scripts/east_asian/ingest_blue_dragon.py

echo "5. Ingesting Japan Academy Film Prize..."
$PYTHON_CMD scripts/east_asian/ingest_japan_academy.py

echo "6. Ingesting Golden Horse Awards..."
$PYTHON_CMD scripts/east_asian/ingest_golden_horse.py

echo "7. Ingesting Hong Kong Film Awards..."
$PYTHON_CMD scripts/east_asian/ingest_hkfa.py

echo "8. Enriching East Asian Films from TMDb..."
$PYTHON_CMD scripts/east_asian/enrich_east_asian_tmdb.py

echo "9. Updating Parasite Global Tracker..."
$PYTHON_CMD scripts/east_asian/parasite_tracker.py

echo "East Asian Pipeline Complete!"
