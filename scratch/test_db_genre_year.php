<?php
require __DIR__ . '/../config/DB.php';
$pdo = DB::connection();
echo "Non-empty genres: " . $pdo->query("SELECT COUNT(*) FROM films WHERE genre IS NOT NULL AND genre != ''")->fetchColumn() . "\n";
$first5 = $pdo->query("SELECT genre FROM films WHERE genre IS NOT NULL AND genre != '' LIMIT 5")->fetchAll(PDO::FETCH_COLUMN);
echo "Some genres: " . implode(', ', $first5) . "\n";
