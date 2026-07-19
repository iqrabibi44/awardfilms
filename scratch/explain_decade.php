<?php
require_once __DIR__ . '/../config/DB.php';
$pdo = DB::connection();

$stmt = $pdo->prepare('
    EXPLAIN SELECT f.id AS filmId, f.slug AS filmSlug, f.title AS filmTitle, f.year AS filmYear, f.poster_url AS filmPosterUrl,
           COUNT(CASE WHEN n.is_winner = 1 THEN 1 END) AS wins,
           COUNT(*) AS noms
    FROM films f
    INNER JOIN nominations n ON f.id = n.film_id
    WHERE f.year >= :startY AND f.year <= :endY
    GROUP BY f.id
    HAVING COUNT(CASE WHEN n.is_winner = 1 THEN 1 END) > 0
    ORDER BY COUNT(*) DESC
    LIMIT :lim OFFSET :off
');

$stmt->bindValue(':startY', 1990, PDO::PARAM_INT);
$stmt->bindValue(':endY', 1999, PDO::PARAM_INT);
$stmt->bindValue(':lim', 24, PDO::PARAM_INT);
$stmt->bindValue(':off', 0, PDO::PARAM_INT);
$stmt->execute();
print_r($stmt->fetchAll());
