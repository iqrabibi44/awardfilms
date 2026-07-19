<?php
require_once __DIR__ . '/../config/DB.php';
$pdo = DB::connection();

echo "=== FILM POSTERS STATS ===\n";
$totalFilms = $pdo->query("SELECT COUNT(*) FROM films")->fetchColumn();
$nullOrEmptyPosters = $pdo->query("SELECT COUNT(*) FROM films WHERE poster_url IS NULL OR poster_url = ''")->fetchColumn();
$hasPosters = $pdo->query("SELECT COUNT(*) FROM films WHERE poster_url IS NOT NULL AND poster_url != ''")->fetchColumn();

echo "Total films: $totalFilms\n";
echo "Films with poster_url: $hasPosters\n";
echo "Films with empty/null poster_url: $nullOrEmptyPosters\n";

echo "\nSample poster URLs in the database:\n";
$stmt = $pdo->query("SELECT id, title, poster_url FROM films WHERE poster_url IS NOT NULL AND poster_url != '' LIMIT 15");
foreach ($stmt->fetchAll() as $row) {
    echo "  - ID: {$row['id']} | Title: {$row['title']} | URL: {$row['poster_url']}\n";
}

echo "\nCheck if any poster URLs are broken TMDB templates (e.g. placeholders or local relative paths):\n";
$stmt2 = $pdo->query("SELECT COUNT(*) FROM films WHERE poster_url NOT LIKE 'http%' AND poster_url IS NOT NULL AND poster_url != ''");
$relativePosters = $stmt2->fetchColumn();
echo "Films with non-http poster URLs: $relativePosters\n";

if ($relativePosters > 0) {
    $stmt3 = $pdo->query("SELECT id, title, poster_url FROM films WHERE poster_url NOT LIKE 'http%' AND poster_url IS NOT NULL AND poster_url != '' LIMIT 5");
    foreach ($stmt3->fetchAll() as $row) {
        echo "  - ID: {$row['id']} | Title: {$row['title']} | URL: {$row['poster_url']}\n";
    }
}
