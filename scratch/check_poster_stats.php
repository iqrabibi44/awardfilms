<?php
require_once __DIR__ . '/../lib/queries.php';
$pdo = DB::connection();
$total = $pdo->query("SELECT COUNT(*) FROM films")->fetchColumn();
$with_poster = $pdo->query("SELECT COUNT(*) FROM films WHERE poster_url IS NOT NULL AND poster_url != ''")->fetchColumn();
echo "Total films: $total\n";
echo "Films with posters: $with_poster\n";
echo "Films without posters: " . ($total - $with_poster) . "\n";

$no_posters = $pdo->query("SELECT title, year FROM films WHERE poster_url IS NULL OR poster_url = '' LIMIT 15")->fetchAll(PDO::FETCH_ASSOC);
echo "\nSample films missing posters:\n";
print_r($no_posters);
?>
