<?php
// scratch/check_filmfare_decorated.php
require_once __DIR__ . '/../config/DB.php';
$pdo = DB::connection();

echo "=== ORIGINAL QUERY FOR MOST DECORATED PERSON (Filmfare) ===\n";
$stmt = $pdo->prepare('
    SELECT p.name, COUNT(*) AS win_count
    FROM nominations n
    JOIN persons p ON n.person_id = p.id
    JOIN editions e ON n.edition_id = e.id
    JOIN ceremonies c ON e.ceremony_id = c.id
    WHERE c.slug = :slug AND n.is_winner = 1
    GROUP BY p.id, p.name
    ORDER BY win_count DESC
    LIMIT 1
');
$stmt->execute([':slug' => 'filmfare-awards']);
print_r($stmt->fetch(PDO::FETCH_ASSOC));

echo "\n=== QUERY FOR MOST DECORATED FILM (Filmfare) ===\n";
$stmt = $pdo->prepare('
    SELECT f.title, e.year, COUNT(*) AS win_count
    FROM nominations n
    JOIN films f ON n.film_id = f.id
    JOIN editions e ON n.edition_id = e.id
    JOIN ceremonies c ON e.ceremony_id = c.id
    WHERE c.slug = :slug AND n.is_winner = 1
    GROUP BY f.id, f.title, e.id, e.year
    ORDER BY win_count DESC
    LIMIT 1
');
$stmt->execute([':slug' => 'filmfare-awards']);
print_r($stmt->fetch(PDO::FETCH_ASSOC));
