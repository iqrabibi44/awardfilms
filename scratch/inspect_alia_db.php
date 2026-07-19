<?php
require_once __DIR__ . '/../lib/queries.php';

$pdo = DB::connection();
$stmt = $pdo->prepare("
    SELECT n.id, n.nominee_text, n.is_winner, f.title AS film_title, f.year AS film_year,
           c.name AS category_name, e.year AS edition_year, cer.name AS ceremony_name
    FROM nominations n
    LEFT JOIN films f ON n.film_id = f.id
    LEFT JOIN categories c ON n.category_id = c.id
    LEFT JOIN editions e ON n.edition_id = e.id
    LEFT JOIN ceremonies cer ON e.ceremony_id = cer.id
    WHERE n.nominee_text LIKE '%Alia Bhatt%'
    LIMIT 5
");
$stmt->execute();
print_r($stmt->fetchAll());
