<?php
require_once __DIR__ . '/config/DB.php';
$pdo = DB::connection();

$stmt = $pdo->query('EXPLAIN 
    SELECT f.id AS filmId, f.title AS filmTitle
    FROM (
        SELECT film_id,
               SUM(is_winner = 1) AS wins,
               COUNT(*) AS noms
        FROM nominations
        GROUP BY film_id
        HAVING wins > 0
        ORDER BY wins DESC
        LIMIT 24 OFFSET 0
    ) n_stats
    INNER JOIN films f ON f.id = n_stats.film_id
    ORDER BY n_stats.wins DESC
');
print_r($stmt->fetchAll());
