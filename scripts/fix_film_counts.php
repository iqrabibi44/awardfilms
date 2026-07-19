<?php
require_once __DIR__ . '/../config/DB.php';

$pdo = DB::connection();

// Add wins_count and noms_count columns if they don't exist
$pdo->exec("ALTER TABLE films ADD COLUMN wins_count INT DEFAULT 0");
$pdo->exec("ALTER TABLE films ADD COLUMN noms_count INT DEFAULT 0");

// Update wins_count (number of winning nominations)
$pdo->exec("UPDATE films f SET wins_count = (SELECT COUNT(*) FROM nominations n WHERE n.film_id = f.id AND n.is_winner = 1)");

// Update noms_count (total nominations)
$pdo->exec("UPDATE films f SET noms_count = (SELECT COUNT(*) FROM nominations n WHERE n.film_id = f.id)");

echo "Film counts updated successfully\n";
?>
