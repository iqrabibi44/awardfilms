<?php
require_once __DIR__ . '/../config/DB.php';

$pdo = DB::connection();
$likeKeyword = '%oscars%';
$limit = 50;
$offset = 0;

function profileQuery($label, $callable) {
    $t = microtime(true);
    $res = $callable();
    $d = microtime(true) - $t;
    echo "$label took: {$d}s\n";
    return $res;
}

profileQuery("1. Film title direct", function() use ($pdo, $likeKeyword) {
    $stmt = $pdo->prepare('SELECT id FROM films WHERE title LIKE :kw LIMIT 200');
    $stmt->bindValue(':kw', $likeKeyword);
    $stmt->execute();
    return $stmt->fetchAll(PDO::FETCH_COLUMN);
});

profileQuery("2. Person matching (two-step)", function() use ($pdo, $likeKeyword) {
    $stmt = $pdo->prepare('SELECT id FROM persons WHERE name LIKE :kw LIMIT 100');
    $stmt->bindValue(':kw', $likeKeyword);
    $stmt->execute();
    $personIds = $stmt->fetchAll(PDO::FETCH_COLUMN);
    if (!empty($personIds)) {
        $placeholders = implode(',', array_fill(0, count($personIds), '?'));
        $stmt = $pdo->prepare("SELECT DISTINCT film_id FROM nominations WHERE person_id IN ($placeholders) LIMIT 200");
        $stmt->execute($personIds);
        return $stmt->fetchAll(PDO::FETCH_COLUMN);
    }
    return [];
});

profileQuery("3. Nominee text matching", function() use ($pdo, $likeKeyword) {
    $stmt = $pdo->prepare('SELECT DISTINCT film_id FROM nominations WHERE nominee_text LIKE :kw LIMIT 200');
    $stmt->bindValue(':kw', $likeKeyword);
    $stmt->execute();
    return $stmt->fetchAll(PDO::FETCH_COLUMN);
});

profileQuery("4. Category matching (two-step)", function() use ($pdo, $likeKeyword) {
    $stmt = $pdo->prepare('SELECT id FROM categories WHERE name LIKE :kw LIMIT 100');
    $stmt->bindValue(':kw', $likeKeyword);
    $stmt->execute();
    $catIds = $stmt->fetchAll(PDO::FETCH_COLUMN);
    if (!empty($catIds)) {
        $placeholders = implode(',', array_fill(0, count($catIds), '?'));
        $stmt = $pdo->prepare("SELECT DISTINCT film_id FROM nominations WHERE category_id IN ($placeholders) LIMIT 200");
        $stmt->execute($catIds);
        return $stmt->fetchAll(PDO::FETCH_COLUMN);
    }
    return [];
});

profileQuery("5. Persons direct query", function() use ($pdo, $likeKeyword, $limit, $offset) {
    $stmt = $pdo->prepare('
        SELECT id, slug, name, photo_url AS photoUrl
        FROM persons
        WHERE name LIKE :kw
        LIMIT :lim OFFSET :off
    ');
    $stmt->bindValue(':kw', $likeKeyword);
    $stmt->bindValue(':lim', $limit, PDO::PARAM_INT);
    $stmt->bindValue(':off', $offset, PDO::PARAM_INT);
    $stmt->execute();
    return $stmt->fetchAll();
});

profileQuery("6. Ceremonies DB search", function() use ($pdo, $likeKeyword, $limit, $offset) {
    $stmt = $pdo->prepare('
        SELECT id, slug, name, country
        FROM ceremonies
        WHERE name LIKE :q
        LIMIT :lim OFFSET :off
    ');
    $stmt->bindValue(':q', $likeKeyword);
    $stmt->bindValue(':lim', $limit, PDO::PARAM_INT);
    $stmt->bindValue(':off', $offset, PDO::PARAM_INT);
    $stmt->execute();
    return $stmt->fetchAll();
});
