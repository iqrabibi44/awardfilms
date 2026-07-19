<?php
require_once __DIR__ . '/../config/DB.php';
$pdo = DB::connection();

// Get 15 films: 5 known to have posters, 10 random missing
$stmt = $pdo->query("
    (SELECT id, title, poster_url, tmdb_id FROM films WHERE poster_url IS NOT NULL AND poster_url != '' LIMIT 5)
    UNION ALL
    (SELECT id, title, poster_url, tmdb_id FROM films WHERE poster_url IS NULL LIMIT 10)
");
$films = $stmt->fetchAll(PDO::FETCH_ASSOC);

echo "Testing img-proxy.php on 15 films...\n\n";

foreach ($films as $film) {
    $url = "http://localhost:8000/img-proxy.php?film=" . $film['id'];
    
    // Request 1: Fresh Load
    $start = microtime(true);
    $headers1 = get_headers($url, 1);
    $time1 = round((microtime(true) - $start) * 1000);
    $type1 = $headers1['Content-Type'] ?? 'Unknown';
    $cacheControl1 = $headers1['Cache-Control'] ?? 'Unknown';

    // Request 2: Cache Load
    $start2 = microtime(true);
    $headers2 = get_headers($url, 1);
    $time2 = round((microtime(true) - $start2) * 1000);
    $type2 = $headers2['Content-Type'] ?? 'Unknown';

    echo "Film ID {$film['id']} - {$film['title']} (Stored URL: " . ($film['poster_url'] ?: 'NULL') . ")\n";
    echo "  Load 1 (Fresh): {$time1}ms | Content-Type: $type1 | Cache-Control: $cacheControl1\n";
    echo "  Load 2 (Cache): {$time2}ms | Content-Type: $type2\n";
    
    if (strpos($type1, 'svg') !== false) {
        echo "  -> Result: 🎬 SVG Placeholder Served\n";
    } else {
        echo "  -> Result: 🖼️ JPEG Poster Served via Proxy\n";
        // Verify cache file exists
        $cacheFile = __DIR__ . '/../cache/posters/' . $film['id'] . '.jpg';
        if (file_exists($cacheFile)) {
            echo "  -> Cache File Written: OK (Size: " . filesize($cacheFile) . " bytes)\n";
        } else {
            echo "  -> Cache File Written: FAILED\n";
        }
    }
    echo "---------------------------------------------------------\n";
}
