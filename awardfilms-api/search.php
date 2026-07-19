<?php
header('Content-Type: application/json');
require_once __DIR__ . '/../lib/queries.php';

$query = $_GET['q'] ?? '';

if (strlen(trim($query)) < 2) {
    echo json_encode(['results' => []]);
    exit;
}

try {
    $data = searchAll($query, 6, 0, 'all');

    $results = [];

    if (!empty($data['intent_message'])) {
        $results[] = [
            'url' => '/search?q=' . urlencode($query),
            'title' => '🤖 AI Assistant',
            'subtitle' => $data['intent_message']
        ];
    }

    // Add ceremonies
    if (!empty($data['ceremonies'])) {
        foreach ($data['ceremonies'] as $c) {
            $results[] = [
                'url' => '/search?q=' . urlencode($c['name']),
                'title' => $c['name'],
                'subtitle' => 'Award Ceremony'
            ];
        }
    }

    // Add films
    if (!empty($data['films'])) {
        foreach ($data['films'] as $f) {
            $subtitle = 'Film' . ($f['year'] ? ' (' . $f['year'] . ')' : '');
            if (!empty($f['category_name']) && !empty($f['ceremony_name'])) {
                $subtitle = $f['category_name'] . ' (' . $f['ceremony_name'] . ' ' . ($f['edition_year'] ?? $f['year']) . ')';
            }
            $results[] = [
                'url' => '/films/' . $f['slug'],
                'title' => $f['title'],
                'subtitle' => $subtitle
            ];
        }
    }

    // Add persons
    if (!empty($data['persons'])) {
        foreach ($data['persons'] as $p) {
            $results[] = [
                'url' => '/persons/' . $p['slug'],
                'title' => $p['name'],
                'subtitle' => 'Person'
            ];
        }
    }

    // Limit to top 8 total results for dropdown
    echo json_encode(['results' => array_slice($results, 0, 8)]);
} catch (Exception $e) {
    echo json_encode(['results' => [], 'error' => $e->getMessage()]);
}
