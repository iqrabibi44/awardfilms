<?php
require 'config/DB.php';
$pdo = DB::connection();
try {
    $pdo->exec('ALTER TABLE persons ADD COLUMN image_url VARCHAR(255) DEFAULT NULL');
    echo "Column image_url added to persons table.\n";
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
