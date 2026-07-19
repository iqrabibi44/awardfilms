<?php
require 'config/DB.php';
$pdo = DB::connection();
$res = $pdo->query('SELECT title, genre, country FROM films LIMIT 5')->fetchAll(PDO::FETCH_ASSOC);
print_r($res);
