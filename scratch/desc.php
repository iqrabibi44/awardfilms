<?php
require_once __DIR__ . '/../config/DB.php';
$pdo = DB::connection();
$stmt = $pdo->query("DESCRIBE nominations");
print_r($stmt->fetchAll());
