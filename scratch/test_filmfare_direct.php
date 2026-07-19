<?php
require 'config/DB.php';
$pdo=DB::connection();
$stmt=$pdo->prepare('SELECT * FROM ceremonies WHERE slug=?');
$stmt->execute(['filmfare']);
var_dump($stmt->fetchAll());
