<?php
require 'config/DB.php';
$pdo=DB::connection();
$stmt=$pdo->prepare('SELECT slug FROM ceremonies');
$stmt->execute();
print_r($stmt->fetchAll(PDO::FETCH_COLUMN));
