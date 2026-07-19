<?php
require_once __DIR__ . '/config/DB.php';

$pdo = DB::connection();

$queries = [
    // Index on is_winner and category_id for getRecentWinners
    "CREATE INDEX idx_nom_is_winner ON nominations (is_winner);",
    "CREATE INDEX idx_nom_category_id ON nominations (category_id);",
    "CREATE INDEX idx_cat_name ON categories (name(255));",

    // Indexes for listAwardWinningFilms and Persons
    "CREATE INDEX idx_nom_film_winner ON nominations (film_id, is_winner);",
    "CREATE INDEX idx_nom_person_winner ON nominations (person_id, is_winner);"
];

foreach ($queries as $q) {
    try {
        echo "Executing: $q\n";
        $pdo->exec($q);
        echo "Success\n";
    } catch (Exception $e) {
        echo "Error: " . $e->getMessage() . "\n";
    }
}
