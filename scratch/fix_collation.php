<?php
require __DIR__ . '/../config/DB.php';
$pdo = DB::connection();

$tables = $pdo->query("SHOW TABLES")->fetchAll(PDO::FETCH_COLUMN);
foreach ($tables as $table) {
    $cols = $pdo->query("SHOW FULL COLUMNS FROM `$table`")->fetchAll();
    foreach ($cols as $col) {
        if ($col['Collation'] && strpos($col['Collation'], 'utf8mb4') === false) {
            echo "Converting $table.{$col['Field']} (was {$col['Collation']})\n";
            $pdo->exec("ALTER TABLE `$table` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
            break; // Whole table converted
        }
    }
}
echo "DB Collation check complete.\n";
