<?php
require_once __DIR__ . '/../lib/queries.php';

$query = "alia bhatt movies for which she won awards";
echo "Original Query: $query\n";

$intent = parseSearchIntent($query);
echo "Parsed Intent:\n";
print_r($intent);

$results = searchAll($query);
echo "\nSearch Results count: " . count($results['films']) . "\n";
foreach ($results['films'] as $f) {
    echo "Film: " . $f['title'] . " (" . $f['year'] . ")\n";
}
echo "\nIntent Message: " . $results['intent_message'] . "\n";
