<?php
require_once __DIR__ . '/../config/DB.php';
$pdo = DB::connection();

$tables = ['nominations', 'films', 'persons', 'categories', 'editions', 'ceremonies'];
foreach ($tables as $t) {
    echo "\nIndexes on $t:\n";
    $stmt = $pdo->query("SHOW INDEXES FROM $t");
    while ($row = $stmt->fetch()) {
        echo "- " . $row['Key_name'] . " (column: " . $row['Column_name'] . ")\n";
    }
}

