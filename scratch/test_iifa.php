<?php
require 'config/DB.php';
$pdo=DB::connection();
$stmt=$pdo->prepare('SELECT * FROM ceremonies WHERE slug=?');
$stmt->execute(['iifa']);
var_dump($stmt->fetchAll());
