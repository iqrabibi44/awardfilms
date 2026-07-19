<?php
require_once __DIR__ . '/../config/DB.php';

$pdo = DB::connection();

function explainQuery($label, $sql, $params = []) {
    global $pdo;
    echo "=== EXPLAIN: $label ===\n";
    $stmt = $pdo->prepare("EXPLAIN $sql");
    $stmt->execute($params);
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
    foreach ($rows as $row) {
        print_r($row);
    }
    echo "\n";
}

explainQuery("getFilmsByDecade", '
        SELECT f.id AS filmId, f.slug AS filmSlug, f.title AS filmTitle, f.year AS filmYear, f.poster_url AS filmPosterUrl,
               COUNT(CASE WHEN n.is_winner = 1 THEN 1 END) AS wins,
               COUNT(*) AS noms
        FROM films f
        INNER JOIN nominations n ON f.id = n.film_id
        WHERE f.year >= :startY AND f.year <= :endY
        GROUP BY f.id
        HAVING COUNT(CASE WHEN n.is_winner = 1 THEN 1 END) > 0
        ORDER BY COUNT(*) DESC
        LIMIT :lim
', [':startY' => 1990, ':endY' => 1999, ':lim' => 24]);
