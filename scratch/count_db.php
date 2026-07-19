<?php
require_once __DIR__ . '/../config/DB.php';
$pdo = DB::connection();
$count = $pdo->query("SELECT COUNT(*) FROM ceremonies")->fetchColumn();
echo "Total ceremonies in DB: $count\n";

$countCat = $pdo->query("SELECT COUNT(*) FROM categories")->fetchColumn();
echo "Total categories in DB: $countCat\n";

$countWin = $pdo->query("SELECT COUNT(*) FROM nominations")->fetchColumn();
echo "Total nominations in DB: $countWin\n";
