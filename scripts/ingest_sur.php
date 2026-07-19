<?php
/**
 * Direct CSV ingest for Premios Sur Awards.
 * Run from: c:\Users\INFOTECH\OneDrive\Desktop\Awardfilms\scripts\
 */
require_once __DIR__ . '/../lib/csv_importer.php';

$csvFile = __DIR__ . '/sur_raw.csv';

if (!file_exists($csvFile)) {
    die("CSV file not found: $csvFile\n");
}

echo "Ingesting " . $csvFile . "...\n";
$start = microtime(true);

try {
    $stats = CSVImporter::import($csvFile);
    echo "\n=== Results ===\n";
    echo "Total rows:             " . $stats['total_rows'] . "\n";
    echo "Skipped rows:           " . $stats['skipped_rows'] . "\n";
    echo "Ceremonies created:     " . $stats['ceremonies_created'] . "\n";
    echo "Editions created:       " . $stats['editions_created'] . "\n";
    echo "Categories created:     " . $stats['categories_created'] . "\n";
    echo "Films created:          " . $stats['films_created'] . "\n";
    echo "Persons created:        " . $stats['persons_created'] . "\n";
    echo "Nominations inserted:   " . $stats['nominations_inserted'] . "\n";
    echo "Nominations updated:    " . $stats['nominations_updated'] . "\n";

    if (!empty($stats['errors'])) {
        echo "\nErrors:\n";
        foreach (array_slice($stats['errors'], 0, 10) as $err) {
            echo "  - " . $err . "\n";
        }
    }
} catch (Exception $e) {
    echo "Fatal: " . $e->getMessage() . "\n";
}

echo "\nDone in " . round(microtime(true) - $start, 2) . "s\n";
