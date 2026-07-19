<?php
header('Content-Type: application/json');
require_once __DIR__ . '/../../config/DB.php';
require_once __DIR__ . '/../../lib/queries.php';

$ceremonySlug = $_GET['ceremony'] ?? '';
$year = isset($_GET['year']) ? (int)$_GET['year'] : 0;

if (!$ceremonySlug || !$year) {
    echo json_encode(null);
    exit;
}

try {
    $pdo = DB::connection();
    
    // Resolve ceremony slug
    $resolvedSlug = resolveSlug($ceremonySlug);
    
    // Get ceremony and edition details
    $stmt = $pdo->prepare("
        SELECT e.venue, e.host, e.id AS edition_id
        FROM editions e
        JOIN ceremonies c ON e.ceremony_id = c.id
        WHERE c.slug = ? AND e.year = ?
        LIMIT 1
    ");
    $stmt->execute([$resolvedSlug, $year]);
    $edition = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$edition) {
        echo json_encode(null);
        exit;
    }
    
    // Get top 3 winners
    $stmt = $pdo->prepare("
        SELECT cat.name AS category_name, f.title AS film_title, p.name AS person_name, n.nominee_text
        FROM nominations n
        JOIN categories cat ON n.category_id = cat.id
        LEFT JOIN films f ON n.film_id = f.id
        LEFT JOIN persons p ON n.person_id = p.id
        WHERE n.edition_id = ? AND n.is_winner = 1
        LIMIT 3
    ");
    $stmt->execute([$edition['edition_id']]);
    $winners = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    $topWinners = [];
    foreach ($winners as $w) {
        $catLower = strtolower($w['category_name']);
        $personKeywords = ['actor', 'actress', 'director', 'singer', 'lyricist', 'writer', 'music', 'performance', 'face', 'debut', 'screenplay', 'story', 'lyrics', 'choreographer', 'cinematographer', 'editor', 'sound', 'composer', 'comedy', 'villain', 'jodi', 'pair', 'comedian', 'person', 'male', 'female', 'host'];
        $isPersonCat = false;
        foreach ($personKeywords as $kw) {
            if (strpos($catLower, $kw) !== false) {
                $isPersonCat = true;
                break;
            }
        }
        
        $personName = $w['person_name'] ?: ($w['nominee_text'] ?: '');
        $filmTitle = $w['film_title'] ?: '';
        
        if ($isPersonCat) {
            $wText = $personName;
            if ($filmTitle && strtolower($filmTitle) !== strtolower($personName)) {
                $wText .= " ($filmTitle)";
            }
        } else {
            $wText = $filmTitle ?: $personName;
        }
        
        $topWinners[] = [
            'category_name' => $w['category_name'],
            'winner_text' => $wText ?: 'Winner'
        ];
    }
    
    $response = [
        'venue' => $edition['venue'],
        'host' => $edition['host'],
        'top_winners' => $topWinners
    ];
    
    echo json_encode($response);
} catch (Exception $e) {
    echo json_encode(['error' => $e->getMessage()]);
}
?>
