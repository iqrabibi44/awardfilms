<?php
require_once __DIR__ . '/../config/DB.php';
require_once __DIR__ . '/../lib/navigation.php';

function testResolveSlug($slug) {
    $slugMap = [
        'siima-awards-telugu' => 'siima-awards',
        'siima-awards-tamil' => 'siima-awards',
        'siima-awards-malayalam' => 'siima-awards',
        'siima-awards-kannada' => 'siima-awards',
        'filmfare-awards-south-malayalam' => 'filmfare-awards-south',
        'filmfare-awards-south-kannada' => 'filmfare-awards-south',
        'filmfare-awards' => 'filmfare',
        'iifa-awards' => 'iifa',
        'producers-guild-film-awards' => 'producers-guild',
        'apsara-film-awards' => 'producers-guild',
        'diosa-de-plata' => 'diosas-de-plata',
        'mexican-cinema-journalists' => 'diosas-de-plata',
        'grande-otelo-awards' => 'grande-premio-do-cinema-brasileiro',
        'brazilian-cinema-awards' => 'grande-premio-do-cinema-brasileiro',
        'rio-iff-awards' => 'festival-do-rio',
        'sur-awards' => 'premios-sur',
        'antalya-golden-orange' => 'antalya-golden-orange-film-awards',
        // Manual additions to test
        'oscars' => 'academy-awards',
    ];
    
    if (isset($slugMap[$slug])) return $slugMap[$slug];
    
    $pdo = DB::connection();
    
    // exact
    $stmt = $pdo->prepare('SELECT slug FROM ceremonies WHERE slug = ? LIMIT 1');
    $stmt->execute([$slug]);
    if ($res = $stmt->fetchColumn()) return $res;
    
    // fallback
    $clean = str_replace(['-awards', '-film-festival', '-prize'], '', $slug);
    $searchTerm = '%' . str_replace('-', '%', $clean) . '%';
    $stmt2 = $pdo->prepare('SELECT slug FROM ceremonies WHERE slug LIKE ? OR name LIKE ? LIMIT 1');
    $stmt2->execute([$searchTerm, $searchTerm]);
    if ($res = $stmt2->fetchColumn()) return $res;
    
    return $slug;
}

$not_found = [];
foreach ($NAV_DATA as $region) {
    foreach ($region['industries'] as $ind) {
        foreach ($ind['ceremonies'] as $cer) {
            $resolved = testResolveSlug($cer['slug']);
            
            $pdo = DB::connection();
            $stmt = $pdo->prepare('SELECT name FROM ceremonies WHERE slug = ?');
            $stmt->execute([$resolved]);
            $dbName = $stmt->fetchColumn();
            
            if (!$dbName) {
                $not_found[] = $cer['name'] . " (" . $cer['slug'] . ") => resolved to " . $resolved;
            }
        }
    }
}

if (empty($not_found)) {
    echo "All navigation slugs resolved to a DB ceremony successfully!\n";
} else {
    echo "Mismatches:\n";
    print_r($not_found);
}
