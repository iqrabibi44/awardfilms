<?php
require_once __DIR__ . '/../config/DB.php';
$pdo = DB::connection();
foreach (['films', 'persons', 'categories', 'nominations', 'ceremonies', 'editions'] as $table) {
    $count = $pdo->query("SELECT COUNT(*) FROM $table")->fetchColumn();
    echo "$table: $count\n";
}
