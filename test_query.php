<?php
require_once __DIR__ . '/config/DB.php';
$pdo = DB::connection();

require_once __DIR__ . '/lib/queries.php';
require_once __DIR__ . '/lib/queries.php';
$pdo = DB::connection();
$entityKeyword = 'best actress (filmfare  )';
$queryYear = 2016;
$limit = 50;
$offset = 0;

$r1 = $pdo->exec("UPDATE ceremonies SET slug = 'guadalajara-iff' WHERE slug = 'guadalajara-iff-awards'");
$r2 = $pdo->exec("UPDATE editions SET slug = REPLACE(slug, 'guadalajara-iff-awards', 'guadalajara-iff') WHERE slug LIKE 'guadalajara-iff-awards%'");

echo "Update complete!\n";
echo "Ceremonies updated: $r1\n";
echo "Editions updated: $r2\n";
?>
