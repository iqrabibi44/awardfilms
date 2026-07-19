<?php
// scratch/compare_ceremonies.php
require_once __DIR__ . '/../lib/navigation.php';
require_once __DIR__ . '/../config/DB.php';
$pdo = DB::connection();

$dbCeremonies = $pdo->query("SELECT id, name, slug FROM ceremonies")->fetchAll(PDO::FETCH_ASSOC);
$dbSlugs = array_column($dbCeremonies, 'slug');

echo "=== CEREMONIES IN NAV BUT NOT IN DB ===\n";
foreach ($NAV_DATA as $cat) {
    foreach ($cat['industries'] as $ind) {
        foreach ($ind['ceremonies'] as $c) {
            if (!in_array($c['slug'], $dbSlugs)) {
                echo "Slug: {$c['slug']} | Name: {$c['name']} (Industry: {$ind['name']})\n";
            }
        }
    }
}
