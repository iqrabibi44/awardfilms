<?php
require 'config/DB.php';
$pdo=DB::connection(); 
$stmt=$pdo->query('SELECT slug FROM ceremonies'); 
$res=$stmt->fetchAll(PDO::FETCH_COLUMN); 
var_dump(in_array('filmfare', $res)); 
var_dump(in_array('filmfare-awards', $res));
