<?php
// awardfilms-api/suggest.php
header('Content-Type: application/json');
require_once __DIR__ . '/../config/DB.php';
require_once __DIR__ . '/../lib/searchAliases.php';
require_once __DIR__ . '/../lib/searchIntents.php';
require_once __DIR__ . '/../lib/queryParser.php';

$query = $_GET['q'] ?? '';

if (strlen(trim($query)) < 2) {
    echo json_encode(['films' => [], 'people' => [], 'ceremonies' => []]);
    exit;
}

try {
    $pdo = DB::connection();
    $aliases = SearchAliases::getAliases();
    $queryLower = strtolower(trim($query));

    $filmsMatched = [];
    $peopleMatched = [];
    $ceremoniesMatched = [];

    // 1. Match ceremonies
    foreach ($aliases['ceremonies'] as $alias => $c) {
        if (strpos($alias, $queryLower) !== false) {
            // Find the category/industry path of the ceremony
            // We can search the NAV_DATA if available or fallback to a helper
            // For general lookup, let's construct a direct link
            $ceremoniesMatched[$c['id']] = [
                'name' => $c['name'],
                'url' => '/search?q=' . urlencode($c['name'])
            ];
            if (count($ceremoniesMatched) >= 3) break;
        }
    }

    // 2. Match people
    // 2. Match people
    // First query database directly using REGEXP for word boundary matches
    $stmt = $pdo->prepare("
        SELECT id, name, slug, nationality 
        FROM persons 
        WHERE name REGEXP :q 
        ORDER BY (CASE WHEN name LIKE :start THEN 1 ELSE 2 END), name ASC
        LIMIT 4
    ");
    $stmt->execute([':q' => '[[:<:]]' . preg_quote($queryLower), ':start' => $queryLower . '%']);
    $peopleDb = $stmt->fetchAll(PDO::FETCH_ASSOC);
    foreach ($peopleDb as $p) {
        // Find what they are known for
        $knownForStmt = $pdo->prepare("
            SELECT c.name 
            FROM nominations n 
            JOIN categories c ON n.category_id = c.id 
            WHERE n.person_id = :pid 
            LIMIT 1
        ");
        $knownForStmt->execute([':pid' => $p['id']]);
        $knownFor = $knownForStmt->fetchColumn() ?: ($p['nationality'] ?: 'Artist');

        $peopleMatched[$p['id']] = [
            'name' => $p['name'],
            'knownFor' => $knownFor,
            'url' => '/persons/' . $p['slug']
        ];
    }

    // If we don't have enough, check aliases
    if (count($peopleMatched) < 4) {
        // Sort aliases to put start matches first
        $sortedPersons = $aliases['persons'];
        uksort($sortedPersons, function($a, $b) use ($queryLower) {
            $aStart = (strpos($a, $queryLower) === 0);
            $bStart = (strpos($b, $queryLower) === 0);
            if ($aStart && !$bStart) return -1;
            if (!$aStart && $bStart) return 1;
            return strlen($a) - strlen($b);
        });

        foreach ($sortedPersons as $alias => $p) {
            if (preg_match('/\b' . preg_quote($queryLower, '/') . '/', $alias) && !isset($peopleMatched[$p['id']])) {
                $peopleMatched[$p['id']] = [
                    'name' => $p['name'],
                    'knownFor' => 'Artist',
                    'url' => '/persons/' . $p['slug']
                ];
                if (count($peopleMatched) >= 4) break;
            }
        }
    }

    // 3. Match films
    $stmt = $pdo->prepare("
        SELECT id, title, slug, year 
        FROM films 
        WHERE title REGEXP :q 
        ORDER BY (CASE WHEN title LIKE :start THEN 1 ELSE 2 END), title ASC
        LIMIT 4
    ");
    $stmt->execute([':q' => '[[:<:]]' . preg_quote($queryLower), ':start' => $queryLower . '%']);
    $filmsDb = $stmt->fetchAll(PDO::FETCH_ASSOC);
    foreach ($filmsDb as $f) {
        $filmsMatched[$f['id']] = [
            'title' => $f['title'],
            'year' => $f['year'],
            'url' => '/films/' . $f['slug']
        ];
    }

    if (count($filmsMatched) < 4) {
        $sortedFilms = $aliases['films'];
        usort($sortedFilms, function($a, $b) use ($queryLower) {
            $aTitle = strtolower($a['title']);
            $bTitle = strtolower($b['title']);
            $aStart = (strpos($aTitle, $queryLower) === 0);
            $bStart = (strpos($bTitle, $queryLower) === 0);
            if ($aStart && !$bStart) return -1;
            if (!$aStart && $bStart) return 1;
            return strlen($aTitle) - strlen($bTitle);
        });

        foreach ($sortedFilms as $f) {
            $titleLower = strtolower($f['title']);
            if (preg_match('/\b' . preg_quote($queryLower, '/') . '/', $titleLower) && !isset($filmsMatched[$f['id']])) {
                $filmsMatched[$f['id']] = [
                    'title' => $f['title'],
                    'year' => $f['year'],
                    'url' => '/films/' . $f['slug']
                ];
                if (count($filmsMatched) >= 4) break;
            }
        }
    }

    echo json_encode([
        'films' => array_values($filmsMatched),
        'people' => array_values($peopleMatched),
        'ceremonies' => array_values($ceremoniesMatched)
    ]);
} catch (Exception $e) {
    echo json_encode(['films' => [], 'people' => [], 'ceremonies' => [], 'error' => $e->getMessage()]);
}
