<?php
require_once __DIR__ . '/../config/DB.php';
$pdo = DB::connection();
$stmt = $pdo->query("SELECT * FROM nominations WHERE person LIKE '%alia bhatt%' LIMIT 5");
$res = $stmt->fetchAll();
echo "Alia in nominations: " . count($res) . "\n";
print_r($res);
