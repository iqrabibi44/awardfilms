<?php
require __DIR__ . '/../config/DB.php';
$pdo = DB::connection();

// Decade query count
$decadeCount = $pdo->query("SELECT COUNT(*) FROM films WHERE year BETWEEN 1990 AND 1999")->fetchColumn();
echo "DECADE 1990s: $decadeCount films\n";

// Genre query count
$genreCount = $pdo->query("SELECT COUNT(*) FROM films WHERE genre IS NOT NULL AND genre != ''")->fetchColumn();
echo "GENRE NON-EMPTY: $genreCount films\n";
if ($genreCount > 0) {
    $genres = $pdo->query("SELECT genre FROM films WHERE genre IS NOT NULL AND genre != '' LIMIT 5")->fetchAll(PDO::FETCH_COLUMN);
    echo "GENRE EXAMPLES: " . implode(', ', $genres) . "\n";
}

// Country query count
$countryCount = $pdo->query("SELECT COUNT(*) FROM films WHERE country IS NOT NULL AND country != ''")->fetchColumn();
echo "COUNTRY NON-EMPTY: $countryCount films\n";
if ($countryCount > 0) {
    $countries = $pdo->query("SELECT country FROM films WHERE country IS NOT NULL AND country != '' LIMIT 5")->fetchAll(PDO::FETCH_COLUMN);
    echo "COUNTRY EXAMPLES: " . implode(', ', $countries) . "\n";
}

// Table collations
$tables = $pdo->query("SHOW TABLE STATUS")->fetchAll();
echo "TABLE COLLATIONS:\n";
foreach ($tables as $t) {
    echo $t['Name'] . " -> " . $t['Collation'] . "\n";
}
