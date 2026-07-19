<?php
require __DIR__ . '/../config/DB.php';
$pdo = DB::connection();
$res = $pdo->query('SELECT title, year, country FROM films LIMIT 5')->fetchAll();
print_r($res);
