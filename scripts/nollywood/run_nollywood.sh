#!/bin/bash
# scripts/nollywood/run_nollywood.sh

echo "Starting Nollywood & African Cinema Pipeline..."

PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo "1. Seeding Ceremonies..."
$PYTHON_CMD scripts/nollywood/seed_ceremonies.py

echo "2. Ingesting AMAA Awards..."
$PYTHON_CMD scripts/nollywood/ingest_amaa.py

echo "3. Ingesting AMVCA Awards..."
$PYTHON_CMD scripts/nollywood/ingest_amvca.py

echo "4. Ingesting FESPACO..."
$PYTHON_CMD scripts/nollywood/ingest_fespaco.py

echo "5. Enriching Nollywood Films from TMDb..."
$PYTHON_CMD scripts/nollywood/enrich_nollywood_tmdb.py

echo "6. Enriching with Wikidata..."
$PYTHON_CMD scripts/nollywood/wikidata_enrich.py

echo "7. Generating Database Stats..."
$PYTHON_CMD scripts/nollywood/db_stats_nollywood.py

echo "Nollywood Pipeline Complete!"
