<?php
require_once __DIR__ . '/../config/DB.php';
require_once __DIR__ . '/../lib/queries.php';

$pdo = DB::connection();
$stmt = $pdo->query('SELECT slug, name FROM ceremonies');
$ceremonies = $stmt->fetchAll(PDO::FETCH_ASSOC);
print_r($ceremonies);
