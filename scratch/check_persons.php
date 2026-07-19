<?php
require __DIR__ . '/../config/DB.php';
$pdo = DB::connection();
$c = $pdo->query('SHOW COLUMNS FROM persons LIKE "image_url"')->fetchAll();
if (empty($c)) {
    echo "No image_url column\n";
} else {
    echo "Has image_url column\n";
    $cnt = $pdo->query('SELECT COUNT(*) FROM persons WHERE image_url IS NOT NULL')->fetchColumn();
    echo "Non-null image_urls: $cnt\n";
}
$cntAll = $pdo->query('SELECT COUNT(*) FROM persons')->fetchColumn();
echo "Total persons: $cntAll\n";
