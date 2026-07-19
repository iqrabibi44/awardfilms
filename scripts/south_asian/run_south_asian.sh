#!/bin/bash
# scripts/south_asian/run_south_asian.sh

echo "Starting Lollywood & South Asian Pipeline..."

PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo "1. Seeding Ceremonies..."
$PYTHON_CMD scripts/south_asian/seed_ceremonies.py

echo "2. Ingesting Lux Style Awards..."
$PYTHON_CMD scripts/south_asian/ingest_lux_style.py

echo "3. Ingesting Historic Nigar Awards..."
$PYTHON_CMD scripts/south_asian/ingest_nigar_awards.py

echo "4. Ingesting ARY & Hum Awards..."
$PYTHON_CMD scripts/south_asian/ingest_ary_hum.py

echo "5. Ingesting Mollywood (Kerala State)..."
$PYTHON_CMD scripts/south_asian/ingest_mollywood.py

echo "6. Ingesting Sandalwood (Karnataka State)..."
$PYTHON_CMD scripts/south_asian/ingest_sandalwood.py

echo "7. Enriching Lollywood Films from TMDb..."
$PYTHON_CMD scripts/south_asian/enrich_lollywood_tmdb.py

echo "8. Updating Eid Blockbuster Tracker..."
$PYTHON_CMD scripts/south_asian/eid_tracker.py

echo "9. Generating Database Stats..."
$PYTHON_CMD scripts/south_asian/db_stats_south_asian.py

echo "South Asian Pipeline Complete!"
