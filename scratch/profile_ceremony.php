<?php
require_once __DIR__ . '/../config/DB.php';
require_once __DIR__ . '/../lib/queries.php';
require_once __DIR__ . '/../lib/navigation.php';

$slug = 'oscars';
$ceremony = getCeremonyBySlug($slug);
if (!$ceremony) {
    die("Ceremony oscars not found in database!\n");
}

$t = microtime(true);

$editionsRaw = getEditionsByCeremonyId($ceremony['id']);
$records = getCeremonyRecords($slug);

$totalEditions = count($editionsRaw);
$yearSpan = $totalEditions > 0
    ? $editionsRaw[$totalEditions - 1]['year'] . '–' . $editionsRaw[0]['year']
    : 'Est. ' . ($ceremony['founded_year'] ?: 1929);

$decadesSet = [];
foreach ($editionsRaw as $e) {
    $dec = (floor($e['year'] / 10) * 10) . 's';
    if (!in_array($dec, $decadesSet)) {
        $decadesSet[] = $dec;
    }
}
usort($decadesSet, fn($a, $b) => strcmp($b, $a));

$editions = [];
$pdo = DB::connection();

$editionIds = array_column($editionsRaw, 'id');
$countsMap = [];
$highlightsMap = [];

if (!empty($editionIds)) {
    $placeholders = implode(',', array_fill(0, count($editionIds), '?'));
    
    // Query 1: Get counts for all editions
    $stmt = $pdo->prepare("
        SELECT edition_id,
               COUNT(DISTINCT category_id) AS total_categories,
               COUNT(*) AS total_nominations,
               COUNT(CASE WHEN is_winner = 1 THEN 1 END) AS total_winners
        FROM nominations
        WHERE edition_id IN ($placeholders)
        GROUP BY edition_id
    ");
    $stmt->execute($editionIds);
    while ($row = $stmt->fetch()) {
        $countsMap[$row['edition_id']] = $row;
    }
    
    // Query 2: Get all winners to select highlights
    $stmt = $pdo->prepare("
        SELECT n.edition_id, cat.name AS category_name, f.title AS film_title, p.name AS person_name
        FROM nominations n
        INNER JOIN categories cat ON n.category_id = cat.id
        LEFT JOIN films f ON n.film_id = f.id
        LEFT JOIN persons p ON n.person_id = p.id
        WHERE n.edition_id IN ($placeholders) AND n.is_winner = 1
    ");
    $stmt->execute($editionIds);
    $allWinners = $stmt->fetchAll();
    
    // Group and sort winners in PHP to pick top 3
    $groupedWinners = [];
    foreach ($allWinners as $w) {
        $groupedWinners[$w['edition_id']][] = $w;
    }
    
    // Priority mapping helper
    $getCategoryPriority = function($name) {
        $nameLower = strtolower($name);
        if (strpos($nameLower, 'best picture') !== false || 
            strpos($nameLower, 'mejor película') !== false || 
            strpos($nameLower, 'best film') !== false || 
            strpos($nameLower, 'mexican film') !== false) {
            return 1;
        }
        if (strpos($nameLower, 'best actor') !== false || 
            strpos($nameLower, 'mejor actor') !== false || 
            strpos($nameLower, 'best performance') !== false || 
            strpos($nameLower, 'mejor interpretación') !== false || 
            strpos($nameLower, 'best actress') !== false || 
            strpos($nameLower, 'mejor actriz') !== false) {
            return 2;
        }
        if (strpos($nameLower, 'best director') !== false || 
            strpos($nameLower, 'mejor dirección') !== false || 
            strpos($nameLower, 'mejor director') !== false) {
            return 3;
        }
        return 4;
    };
    
    foreach ($groupedWinners as $eId => $winnersList) {
        usort($winnersList, function($a, $b) use ($getCategoryPriority) {
            $pA = $getCategoryPriority($a['category_name']);
            $pB = $getCategoryPriority($b['category_name']);
            if ($pA !== $pB) {
                return $pA <=> $pB;
            }
            return strcasecmp($a['category_name'], $b['category_name']);
        });
        $highlightsMap[$eId] = array_slice($winnersList, 0, 3);
    }
}

foreach ($editionsRaw as $e) {
    $counts = $countsMap[$e['id']] ?? [
        'total_categories' => 0,
        'total_nominations' => 0,
        'total_winners' => 0
    ];
    $winners = $highlightsMap[$e['id']] ?? [];

    $editions[] = [
        'id' => $e['id'],
        'year' => (int)$e['year'],
        'edition_number' => $e['edition_number'],
        'venue' => $e['venue'],
        'host' => $e['host'],
        'broadcast_network' => $e['broadcast_network'],
        'slug' => $e['slug'],
        'total_categories' => (int)($counts['total_categories'] ?? 0),
        'total_winners' => (int)($counts['total_winners'] ?? 0),
        'highlight_winners' => array_map(fn($w) => [
            'category_name' => $w['category_name'],
            'film_title' => $w['film_title'] ?: '',
            'person_name' => $w['person_name'] ?: ($w['category_name'] ?: '')
        ], $winners)
    ];
}

$d = microtime(true) - $t;
echo "Simulating ceremony.php for 'oscars' took: {$d}s\n";
echo "Total editions processed: " . count($editions) . "\n";
