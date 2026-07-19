<?php
require_once __DIR__ . '/../config/DB.php';
require_once __DIR__ . '/navigation.php';

function get_cached_query_result($key, $callback, $ttl = 3600) {
    $cacheDir = __DIR__ . '/../cache';
    if (!is_dir($cacheDir)) @mkdir($cacheDir, 0777, true);
    
    $cacheFile = $cacheDir . '/' . md5($key) . '.json';
    
    if (file_exists($cacheFile) && (time() - filemtime($cacheFile)) < $ttl) {
        $data = json_decode(file_get_contents($cacheFile), true);
        if ($data !== null) return $data;
    }
    
    $data = $callback();
    file_put_contents($cacheFile, json_encode($data));
    return $data;
}

function getStats() {
    $pdo = DB::connection();
    $films = $pdo->query('SELECT COUNT(*) FROM films')->fetchColumn();
    $persons = $pdo->query('SELECT COUNT(*) FROM persons')->fetchColumn();
    $nominations = $pdo->query('SELECT COUNT(*) FROM nominations')->fetchColumn();
    $ceremonies = $pdo->query('SELECT COUNT(*) FROM ceremonies')->fetchColumn();
    
    return [
        'films' => (int)$films,
        'persons' => (int)$persons,
        'nominations' => (int)$nominations,
        'ceremonies' => (int)$ceremonies
    ];
}

function getAllCeremonies() {
    $pdo = DB::connection();
    return $pdo->query('SELECT * FROM ceremonies ORDER BY name')->fetchAll();
}

function getCeremonyBySlug($slug) {
    $resolvedSlug = resolveSlug($slug);
    
    $pdo = DB::connection();
    $stmt = $pdo->prepare('SELECT * FROM ceremonies WHERE slug = ? LIMIT 1');
    $stmt->execute([$resolvedSlug]);
    return $stmt->fetch() ?: null;
}

/**
 * Resolves a UI slug to the DB ceremony slug using the same map as getCeremonyBySlug.
 */
function resolveSlug($slug) {
    static $cache = [];
    if (isset($cache[$slug])) return $cache[$slug];

    $slugMap = [
        'siima-awards-telugu' => 'siima-awards',
        'siima-awards-tamil' => 'siima-awards',
        'siima-awards-malayalam' => 'siima-awards',
        'siima-awards-kannada' => 'siima-awards',
        'filmfare-awards-south-malayalam' => 'filmfare-awards-south',
        'filmfare-awards-south-kannada' => 'filmfare-awards-south',
        'producers-guild-film-awards' => 'producers-guild',
        'apsara-film-awards' => 'producers-guild',
        'diosa-de-plata' => 'diosas-de-plata',
        'mexican-cinema-journalists' => 'diosas-de-plata',
        'grande-otelo-awards' => 'grande-premio-do-cinema-brasileiro',
        'brazilian-cinema-awards' => 'grande-premio-do-cinema-brasileiro',
        'rio-iff-awards' => 'festival-do-rio',
        'sur-awards' => 'premios-sur',
        'antalya-golden-orange' => 'antalya-golden-orange-film-awards',
        'oscars' => 'academy-awards',
        'cannes' => 'cannes-film-festival-palme-dor',
        'bafta' => 'bafta-film-awards',
        'biff-awards' => 'busan-international-film-festival-awards',
        'kafc-awards' => 'korean-association-of-film-critics-awards',
        'pisa-awards' => 'pisa',
        'el-gouna-iff' => 'el-gouna-film-festival'
    ];
    
    if (isset($slugMap[$slug])) {
        $cache[$slug] = $slugMap[$slug];
        return $cache[$slug];
    }
    
    // Dynamic DB Fallback
    $pdo = DB::connection();
    
    // 1. Exact match
    $stmt = $pdo->prepare('SELECT slug FROM ceremonies WHERE slug = ? LIMIT 1');
    $stmt->execute([$slug]);
    if ($res = $stmt->fetchColumn()) {
        $cache[$slug] = $res;
        return $res;
    }
    
    // 2. Strict LIKE match (prefer closest/shortest match to avoid false positives)
    $clean = str_replace(['-awards', '-film-festival', '-prize'], '', $slug);
    $searchTerm = '%' . str_replace('-', '%', $clean) . '%';
    
    $stmt2 = $pdo->prepare('SELECT slug FROM ceremonies WHERE slug LIKE ? OR name LIKE ? ORDER BY LENGTH(name) ASC LIMIT 1');
    $stmt2->execute([$searchTerm, $searchTerm]);
    if ($res = $stmt2->fetchColumn()) {
        $cache[$slug] = $res;
        return $res;
    }
    
    $cache[$slug] = $slug;
    return $slug;
}



function getEditionsByCeremonyId($ceremonyId) {
    $pdo = DB::connection();
    $stmt = $pdo->prepare('SELECT * FROM editions WHERE ceremony_id = ? ORDER BY year DESC');
    $stmt->execute([$ceremonyId]);
    return $stmt->fetchAll();
}

function getEditionDetails($ceremonySlug, $year) {
    $ceremonySlug = resolveSlug($ceremonySlug);
    $pdo = DB::connection();
    $stmt = $pdo->prepare('
        SELECT e.* 
        FROM editions e 
        JOIN ceremonies c ON e.ceremony_id = c.id 
        WHERE c.slug = ? AND e.year = ? 
        LIMIT 1
    ');
    $stmt->execute([$ceremonySlug, (int)$year]);
    return $stmt->fetch() ?: null;
}

function getEditionNominations($editionId) {
    $pdo = DB::connection();
    $stmt = $pdo->prepare('
        SELECT n.id AS nominationId, n.nominee_text AS nomineeText, n.is_winner AS isWinner, n.note,
               cat.id AS categoryId, cat.name AS categoryName, cat.department,
               f.id AS filmId, f.title AS filmTitle, f.slug AS filmSlug, f.poster_url AS filmPosterUrl,
               p.id AS personId, p.name AS personName, p.slug AS personSlug
        FROM nominations n
        INNER JOIN categories cat ON n.category_id = cat.id
        LEFT JOIN films f ON n.film_id = f.id
        LEFT JOIN persons p ON n.person_id = p.id
        WHERE n.edition_id = ?
        ORDER BY cat.name ASC, n.is_winner DESC
    ');
    $stmt->execute([$editionId]);
    return $stmt->fetchAll();
}

function getFilmBySlug($slug) {
    $pdo = DB::connection();
    $stmt = $pdo->prepare('SELECT * FROM films WHERE slug = ? LIMIT 1');
    $stmt->execute([$slug]);
    return $stmt->fetch() ?: null;
}

function getPersonBySlug($slug) {
    $pdo = DB::connection();
    $stmt = $pdo->prepare('SELECT * FROM persons WHERE slug = ? LIMIT 1');
    $stmt->execute([$slug]);
    return $stmt->fetch() ?: null;
}

function getFilmWithNominations($slug) {
    $film = getFilmBySlug($slug);
    if (!$film) return null;

    $pdo = DB::connection();
    $stmt = $pdo->prepare('
        SELECT n.id AS nominationId, n.is_winner AS isWinner, n.nominee_text AS nomineeText,
               cat.name AS categoryName, e.year, c.slug AS ceremonySlug, c.name AS ceremonyName
        FROM nominations n
        INNER JOIN editions e ON n.edition_id = e.id
        INNER JOIN ceremonies c ON e.ceremony_id = c.id
        INNER JOIN categories cat ON n.category_id = cat.id
        WHERE n.film_id = ?
        ORDER BY e.year DESC, c.name ASC
    ');
    $stmt->execute([$film['id']]);
    $nominations = $stmt->fetchAll();

    require_once __DIR__ . '/searchAliases.php';
    $aliases = SearchAliases::getAliases();
    $nameLower = strtolower(trim($film['title']));
    $isPerson = isset($aliases['persons'][$nameLower]);

    if ($isPerson) {
        $filtered = [];
        $personName = $film['title'];
        foreach ($nominations as $n) {
            if (stripos($n['nomineeText'], $personName) !== false || stripos($personName, $n['nomineeText']) !== false) {
                $filtered[] = $n;
            }
        }
        $nominations = $filtered;
    }

    // De-duplicate combinations of (categoryName, ceremonySlug, year, isWinner)
    $uniqueNoms = [];
    $seen = [];
    foreach ($nominations as $n) {
        $key = $n['categoryName'] . '|' . $n['ceremonySlug'] . '|' . $n['year'] . '|' . $n['isWinner'];
        if (!isset($seen[$key])) {
            $seen[$key] = true;
            $uniqueNoms[] = $n;
        }
    }
    $nominations = $uniqueNoms;

    $wins = 0;
    foreach ($nominations as $n) {
        if ($n['isWinner']) $wins++;
    }

    return [
        'film' => $film,
        'nominations' => $nominations,
        'wins' => $wins,
        'nominationCount' => count($nominations)
    ];
}

function getPersonWithNominations($slug) {
    $person = getPersonBySlug($slug);
    if (!$person) return null;

    $pdo = DB::connection();
    $stmt = $pdo->prepare('
        SELECT n.id AS nominationId, n.is_winner AS isWinner, n.nominee_text AS nomineeText,
               cat.name AS categoryName, e.year, c.slug AS ceremonySlug, c.name AS ceremonyName,
               f.title AS filmTitle, f.slug AS filmSlug
        FROM nominations n
        INNER JOIN editions e ON n.edition_id = e.id
        INNER JOIN ceremonies c ON e.ceremony_id = c.id
        INNER JOIN categories cat ON n.category_id = cat.id
        LEFT JOIN films f ON n.film_id = f.id
        WHERE n.person_id = ?
        ORDER BY e.year DESC
    ');
    $stmt->execute([$person['id']]);
    $nominations = $stmt->fetchAll();

    // De-duplicate combinations of (categoryName, ceremonySlug, year, isWinner)
    $uniqueNoms = [];
    $seen = [];
    foreach ($nominations as $n) {
        $key = $n['categoryName'] . '|' . $n['ceremonySlug'] . '|' . $n['year'] . '|' . $n['isWinner'];
        if (!isset($seen[$key])) {
            $seen[$key] = true;
            $uniqueNoms[] = $n;
        }
    }
    $nominations = $uniqueNoms;

    $wins = 0;
    foreach ($nominations as $n) {
        if ($n['isWinner']) $wins++;
    }

    return [
        'person' => $person,
        'nominations' => $nominations,
        'wins' => $wins,
        'nominationCount' => count($nominations)
    ];
}

function getRecentWinners($limit = 12) {
    return get_cached_query_result("recent_winners_$limit", function() use ($limit) {
        $pdo = DB::connection();
        // Optimize: Pre-fetch categories
        $catStmt = $pdo->prepare("SELECT id FROM categories WHERE name LIKE '%Best Picture%' OR name LIKE '%Best Film%' OR name LIKE '%best picture%' OR name LIKE '%best film%'");
        $catStmt->execute();
        $catIds = $catStmt->fetchAll(PDO::FETCH_COLUMN);

        if (empty($catIds)) return [];

        $in = str_repeat('?,', count($catIds) - 1) . '?';
        
        $stmt = $pdo->prepare("
            SELECT f.id AS filmId, f.title AS filmTitle, f.slug AS filmSlug, f.poster_url AS filmPosterUrl, f.year AS filmYear,
                   cat.name AS categoryName, c.name AS ceremonyName, c.slug AS ceremonySlug, e.year AS editionYear
            FROM nominations n
            INNER JOIN films f ON n.film_id = f.id
            INNER JOIN categories cat ON n.category_id = cat.id
            INNER JOIN editions e ON n.edition_id = e.id
            INNER JOIN ceremonies c ON e.ceremony_id = c.id
            WHERE n.is_winner = 1
              AND n.category_id IN ($in)
              AND f.title != ''
            ORDER BY e.year DESC
            LIMIT ?
        ");
        $params = $catIds;
        $params[] = $limit;
        $stmt->execute($params);
        return $stmt->fetchAll();
    });
}

function listAwardWinningFilms($limit = 24, $offset = 0) {
    return get_cached_query_result("award_winning_films_{$limit}_{$offset}", function() use ($limit, $offset) {
        $pdo = DB::connection();
        $stmt = $pdo->prepare('
            SELECT f.id AS filmId, f.slug AS filmSlug, f.title AS filmTitle, f.year AS filmYear,
                   f.country AS filmCountry, f.poster_url AS filmPosterUrl,
                   n_stats.wins, n_stats.noms
            FROM (
                SELECT film_id,
                       SUM(is_winner = 1) AS wins,
                       COUNT(*) AS noms
                FROM nominations
                GROUP BY film_id
                HAVING wins > 0
                ORDER BY wins DESC
                LIMIT :lim OFFSET :off
            ) n_stats
            INNER JOIN films f ON f.id = n_stats.film_id
            ORDER BY n_stats.wins DESC
        ');
        $stmt->bindValue(':lim', $limit, PDO::PARAM_INT);
        $stmt->bindValue(':off', $offset, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll();
    });
}

function listAwardWinningPersons($limit = 24, $offset = 0) {
    return get_cached_query_result("award_winning_persons_{$limit}_{$offset}", function() use ($limit, $offset) {
        $pdo = DB::connection();
        $stmt = $pdo->prepare('
            SELECT p.id AS personId, p.slug AS personSlug, p.name AS personName,
                   p.nationality AS personNationality, p.photo_url AS personPhotoUrl,
                   n_stats.wins, n_stats.noms
            FROM (
                SELECT person_id,
                       SUM(is_winner = 1) AS wins,
                       COUNT(*) AS noms
                FROM nominations
                WHERE person_id IS NOT NULL
                GROUP BY person_id
                HAVING wins > 0
                ORDER BY wins DESC
                LIMIT :lim OFFSET :off
            ) n_stats
            INNER JOIN persons p ON p.id = n_stats.person_id
            ORDER BY n_stats.wins DESC
        ');
        $stmt->bindValue(':lim', $limit, PDO::PARAM_INT);
        $stmt->bindValue(':off', $offset, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll();
    });
}

function listCeremoniesWithStats() {
    $pdo = DB::connection();
    return $pdo->query('
        SELECT c.id, c.slug, c.name, c.short_name AS shortName, c.country, c.founded_year AS foundedYear, c.description,
               COUNT(DISTINCT e.id) AS editionCount
        FROM ceremonies c
        LEFT JOIN editions e ON e.ceremony_id = c.id
        GROUP BY c.id
        ORDER BY c.name
    ')->fetchAll();
}

function getFilmsByDecade($startYear, $endYear, $limit = 24, $offset = 0) {
    return get_cached_query_result("films_decade_{$startYear}_{$endYear}_{$limit}_{$offset}", function() use ($startYear, $endYear, $limit, $offset) {
        $pdo = DB::connection();
        $stmt = $pdo->prepare('
            SELECT f.id AS filmId, f.slug AS filmSlug, f.title AS filmTitle, f.year AS filmYear, f.poster_url AS filmPosterUrl,
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
        $stmt->bindValue(':startY', $startYear, PDO::PARAM_INT);
        $stmt->bindValue(':endY', $endYear, PDO::PARAM_INT);
        $stmt->bindValue(':lim', $limit, PDO::PARAM_INT);
        $stmt->bindValue(':off', $offset, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll();
    });
}

function getFilmsByGenre($genre, $limit = 24, $offset = 0) {
    $cleanGenre = preg_replace('/[^a-zA-Z0-9_-]/', '', $genre);
    return get_cached_query_result("films_genre_{$cleanGenre}_{$limit}_{$offset}", function() use ($genre, $limit, $offset) {
        $pdo = DB::connection();
        $stmt = $pdo->prepare('
            SELECT f.id AS filmId, f.slug AS filmSlug, f.title AS filmTitle, f.year AS filmYear, f.poster_url AS filmPosterUrl,
                   COUNT(CASE WHEN n.is_winner = 1 THEN 1 END) AS wins,
                   COUNT(*) AS noms
            FROM films f
            INNER JOIN nominations n ON f.id = n.film_id
            WHERE f.genre LIKE :genre
            GROUP BY f.id
            HAVING COUNT(CASE WHEN n.is_winner = 1 THEN 1 END) > 0
            ORDER BY COUNT(*) DESC
            LIMIT :lim OFFSET :off
        ');
        $stmt->bindValue(':genre', '%' . $genre . '%');
        $stmt->bindValue(':lim', $limit, PDO::PARAM_INT);
        $stmt->bindValue(':off', $offset, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll();
    });
}

function getFilmsByCountry($country, $limit = 24, $offset = 0) {
    $cleanCountry = preg_replace('/[^a-zA-Z0-9_-]/', '', $country);
    return get_cached_query_result("films_country_{$cleanCountry}_{$limit}_{$offset}", function() use ($country, $limit, $offset) {
        $pdo = DB::connection();
        $stmt = $pdo->prepare('
            SELECT f.id AS filmId, f.slug AS filmSlug, f.title AS filmTitle, f.year AS filmYear, f.poster_url AS filmPosterUrl,
                   COUNT(CASE WHEN n.is_winner = 1 THEN 1 END) AS wins,
                   COUNT(*) AS noms
            FROM films f
            INNER JOIN nominations n ON f.id = n.film_id
            WHERE f.country LIKE :country
            GROUP BY f.id
            HAVING COUNT(CASE WHEN n.is_winner = 1 THEN 1 END) > 0
            ORDER BY COUNT(*) DESC
            LIMIT :lim OFFSET :off
        ');
        $stmt->bindValue(':country', '%' . $country . '%');
        $stmt->bindValue(':lim', $limit, PDO::PARAM_INT);
        $stmt->bindValue(':off', $offset, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll();
    });
}

function getCountriesWithFilmCounts() {
    $pdo = DB::connection();
    return $pdo->query('
        SELECT f.country, COUNT(DISTINCT f.id) AS filmCount, COUNT(CASE WHEN n.is_winner = 1 THEN 1 END) AS winCount
        FROM films f
        INNER JOIN nominations n ON f.id = n.film_id
        WHERE f.country IS NOT NULL
        GROUP BY f.country
        ORDER BY COUNT(DISTINCT f.id) DESC
    ')->fetchAll();
}

function getStreamingLinks($filmId) {
    $pdo = DB::connection();
    $stmt = $pdo->prepare('SELECT * FROM streaming_links WHERE film_id = ? ORDER BY platform_name');
    $stmt->execute([$filmId]);
    return $stmt->fetchAll();
}

function getFilmAlternateTitles($filmId) {
    $pdo = DB::connection();
    $stmt = $pdo->prepare('SELECT * FROM film_alternate_titles WHERE film_id = ?');
    $stmt->execute([$filmId]);
    return $stmt->fetchAll();
}

function getFilmAlsoWonIn($filmId) {
    $pdo = DB::connection();
    $stmt = $pdo->prepare('
        SELECT c.slug AS ceremonySlug, c.name AS ceremonyName, c.country AS ceremonyCountry,
               CAST(COUNT(*) AS UNSIGNED) AS wins
        FROM nominations n
        INNER JOIN editions e ON n.edition_id = e.id
        INNER JOIN ceremonies c ON e.ceremony_id = c.id
        WHERE n.film_id = ? AND n.is_winner = 1
        GROUP BY c.slug, c.name, c.country
        ORDER BY COUNT(*) DESC
    ');
    $stmt->execute([$filmId]);
    return $stmt->fetchAll();
}

function getEditionWithAllCategories($ceremonySlug, $year) {
    $ceremonySlug = resolveSlug($ceremonySlug);
    $pdo = DB::connection();
    
    // 1. Get ceremony & edition details
    $stmt = $pdo->prepare('
        SELECT c.id AS ceremonyId, c.name AS ceremonyName, c.slug AS ceremonySlug, c.country AS ceremonyCountry,
               e.id AS editionId, e.year, e.edition_number AS editionNumber, e.date_held AS dateHeld, e.venue, e.host, e.broadcast_network AS broadcastNetwork
        FROM editions e
        INNER JOIN ceremonies c ON e.ceremony_id = c.id
        WHERE c.slug = ? AND e.year = ?
        LIMIT 1
    ');
    $stmt->execute([$ceremonySlug, (int)$year]);
    $ed = $stmt->fetch();
    if (!$ed) return null;

    // 2. Get all nominations for this edition
    $stmt = $pdo->prepare('
        SELECT n.id AS nominationId, n.nominee_text AS nomineeText, n.note, n.is_winner AS isWinner,
               cat.id AS categoryId, cat.name AS categoryName, cat.slug AS categorySlug, cat.department AS categoryDepartment,
               f.id AS filmId, f.title AS filmTitle, f.slug AS filmSlug, f.year AS filmYear, f.poster_url AS filmPosterUrl, f.genre AS filmGenre,
               p.id AS personId, p.name AS personName, p.slug AS personSlug, p.photo_url AS personPhotoUrl, p.nationality AS personNationality
        FROM nominations n
        INNER JOIN categories cat ON n.category_id = cat.id
        LEFT JOIN films f ON n.film_id = f.id
        LEFT JOIN persons p ON n.person_id = p.id
        WHERE n.edition_id = ?
        ORDER BY cat.department ASC, cat.name ASC, n.is_winner DESC
    ');
    $stmt->execute([(int)$ed['editionId']]);
    $noms = $stmt->fetchAll();

    // Group by category
    $categoriesMap = [];
    foreach ($noms as $r) {
        $catId = (int)$r['categoryId'];
        if (!isset($categoriesMap[$catId])) {
            $categoriesMap[$catId] = [
                'id' => $catId,
                'name' => $r['categoryName'],
                'slug' => $r['categorySlug'],
                'department' => $r['categoryDepartment'] ?: 'General',
                'nominations' => []
            ];
        }

        $categoriesMap[$catId]['nominations'][] = [
            'id' => (int)$r['nominationId'],
            'nominee_text' => $r['nomineeText'],
            'note' => $r['note'],
            'is_winner' => (bool)$r['isWinner'],
            'film' => $r['filmId'] ? [
                'title' => $r['filmTitle'],
                'slug' => $r['filmSlug'],
                'year' => $r['filmYear'] ? (int)$r['filmYear'] : null,
                'poster_url' => $r['filmPosterUrl'],
                'genre' => $r['filmGenre']
            ] : null,
            'person' => $r['personId'] ? [
                'name' => $r['personName'],
                'slug' => $r['personSlug'],
                'photo_url' => $r['personPhotoUrl'],
                'nationality' => $r['personNationality']
            ] : null
        ];
    }

    $categories = array_values($categoriesMap);
    usort($categories, function($a, $b) {
        $depA = strtolower($a['department']);
        $depB = strtolower($b['department']);
        if ($depA !== $depB) return strcmp($depA, $depB);
        return strcmp($a['name'], $b['name']);
    });

    $totalWinners = 0;
    foreach ($noms as $n) {
        if ($n['isWinner']) $totalWinners++;
    }

    return [
        'ceremony' => [
            'name' => $ed['ceremonyName'],
            'slug' => $ed['ceremonySlug'],
            'country' => $ed['ceremonyCountry']
        ],
        'edition' => [
            'id' => (int)$ed['editionId'],
            'year' => (int)$ed['year'],
            'edition_number' => $ed['editionNumber'] ? (int)$ed['editionNumber'] : null,
            'date_held' => $ed['dateHeld'],
            'venue' => $ed['venue'],
            'host' => $ed['host'],
            'broadcast_network' => $ed['broadcastNetwork']
        ],
        'categories' => $categories,
        'summary' => [
            'total_categories' => count($categories),
            'total_nominations' => count($noms),
            'total_winners' => $totalWinners
        ]
    ];
}

function getCeremonyRecords($ceremonySlug) {
    $ceremonySlug = resolveSlug($ceremonySlug);
    $pdo = DB::connection();
    
    // 1. Most decorated film in a single edition (excluding placeholders and actor-as-film rows)
    $stmt = $pdo->prepare('
        SELECT f.title, f.slug AS film_slug, e.year, COUNT(*) AS win_count
        FROM nominations n
        JOIN films f ON n.film_id = f.id
        JOIN editions e ON n.edition_id = e.id
        JOIN ceremonies c ON e.ceremony_id = c.id
        JOIN categories cat ON n.category_id = cat.id
        WHERE c.slug = :slug AND n.is_winner = 1
          AND f.title NOT IN ("NO CEREMONY", "No Other Nominee", "No Award", "no film")
          AND cat.name NOT LIKE "%Actor%"
          AND cat.name NOT LIKE "%Actress%"
          AND cat.name NOT LIKE "%Director%"
          AND cat.name NOT LIKE "%Lyricist%"
          AND cat.name NOT LIKE "%Singer%"
          AND cat.name NOT LIKE "%Performance%"
        GROUP BY f.id, f.title, f.slug, e.id, e.year
        ORDER BY win_count DESC, e.year DESC
        LIMIT 1
    ');
    $stmt->execute([':slug' => $ceremonySlug]);
    $mostDecoratedFilm = $stmt->fetch() ?: null;
    if ($mostDecoratedFilm) {
        $mostDecoratedFilm['win_count'] = (int)$mostDecoratedFilm['win_count'];
        $mostDecoratedFilm['year'] = (int)$mostDecoratedFilm['year'];
    }

    // 2. Most total wins (film across all editions)
    $stmt = $pdo->prepare('
        SELECT f.title, f.slug AS film_slug, COUNT(*) AS win_count
        FROM nominations n
        JOIN films f ON n.film_id = f.id
        JOIN editions e ON n.edition_id = e.id
        JOIN ceremonies c ON e.ceremony_id = c.id
        WHERE c.slug = :slug AND n.is_winner = 1
          AND f.title NOT IN ("NO CEREMONY", "No Other Nominee", "No Award", "no film")
        GROUP BY f.id, f.title, f.slug
        ORDER BY win_count DESC
        LIMIT 1
    ');
    $stmt->execute([':slug' => $ceremonySlug]);
    $mostTotalWinsFilm = $stmt->fetch() ?: null;
    if ($mostTotalWinsFilm) $mostTotalWinsFilm['win_count'] = (int)$mostTotalWinsFilm['win_count'];

    // 3. Most decorated person (excluding placeholders, matching person categories)
    $stmt = $pdo->prepare('
        SELECT n.nominee_text AS name, COUNT(*) AS win_count
        FROM nominations n
        JOIN editions e ON n.edition_id = e.id
        JOIN ceremonies c ON e.ceremony_id = c.id
        JOIN categories cat ON n.category_id = cat.id
        WHERE c.slug = :slug AND n.is_winner = 1 AND n.nominee_text != ""
          AND n.nominee_text NOT LIKE "%NO CEREMONY%"
          AND n.nominee_text NOT LIKE "%No Other Nominee%"
          AND n.nominee_text NOT LIKE "%No Award%"
          AND n.nominee_text NOT LIKE "%no film%"
          AND n.nominee_text NOT LIKE "%Actress%"
          AND n.nominee_text NOT LIKE "%Actor%"
          AND (cat.name LIKE "%Actor%" OR cat.name LIKE "%Actress%" OR cat.name LIKE "%Director%" OR cat.name LIKE "%Lyricist%" OR cat.name LIKE "%Music%" OR cat.name LIKE "%Singer%" OR cat.name LIKE "%Performance%" OR cat.name LIKE "%Choreography%" OR cat.name LIKE "%Editing%" OR cat.name LIKE "%Art%" OR cat.name LIKE "%Sound%" OR cat.name LIKE "%Dialogue%" OR cat.name LIKE "%Screenplay%" OR cat.name LIKE "%Story%" OR cat.name LIKE "%Writer%")
        GROUP BY n.nominee_text
        ORDER BY win_count DESC
        LIMIT 1
    ');
    $stmt->execute([':slug' => $ceremonySlug]);
    $mostDecoratedPerson = $stmt->fetch() ?: null;
    if ($mostDecoratedPerson) {
        $mostDecoratedPerson['win_count'] = (int)$mostDecoratedPerson['win_count'];
        
        // Find person_slug or film_slug dynamically for link routing
        require_once __DIR__ . '/searchAliases.php';
        $aliases = SearchAliases::getAliases();
        $nameLower = strtolower(trim($mostDecoratedPerson['name']));
        $mostDecoratedPerson['slug'] = null;
        $mostDecoratedPerson['type'] = 'person';
        
        if (isset($aliases['persons'][$nameLower]) && !empty($aliases['persons'][$nameLower]['slug'])) {
            $mostDecoratedPerson['slug'] = $aliases['persons'][$nameLower]['slug'];
            $mostDecoratedPerson['type'] = 'person';
        } else {
            foreach ($aliases['films'] as $f) {
                if (strtolower($f['title']) === $nameLower) {
                    $mostDecoratedPerson['slug'] = $f['slug'];
                    $mostDecoratedPerson['type'] = 'film';
                    break;
                }
            }
        }
    }

    // 4. Total films honoured (actual database count)
    $stmt = $pdo->prepare('
        SELECT COUNT(DISTINCT n.film_id)
        FROM nominations n
        JOIN editions e ON n.edition_id = e.id
        JOIN ceremonies c ON e.ceremony_id = c.id
        WHERE c.slug = :slug AND n.film_id IS NOT NULL
    ');
    $stmt->execute([':slug' => $ceremonySlug]);
    $totalFilmsHonoured = (int)($stmt->fetchColumn() ?: 0);

    // 5. First edition winner
    $stmt = $pdo->prepare('
        SELECT f.title, e.year, cat.name AS category
        FROM nominations n
        JOIN films f ON n.film_id = f.id
        JOIN editions e ON n.edition_id = e.id
        JOIN categories cat ON n.category_id = cat.id
        JOIN ceremonies c ON e.ceremony_id = c.id
        WHERE c.slug = :slug AND n.is_winner = 1
        ORDER BY e.year ASC, cat.name ASC
        LIMIT 1
    ');
    $stmt->execute([':slug' => $ceremonySlug]);
    $firstEditionWinner = $stmt->fetch() ?: null;
    if ($firstEditionWinner) $firstEditionWinner['year'] = (int)$firstEditionWinner['year'];

    // 6. Latest winner
    $stmt = $pdo->prepare('
        SELECT f.title, e.year, cat.name AS category
        FROM nominations n
        JOIN films f ON n.film_id = f.id
        JOIN editions e ON n.edition_id = e.id
        JOIN categories cat ON n.category_id = cat.id
        JOIN ceremonies c ON e.ceremony_id = c.id
        WHERE c.slug = :slug AND n.is_winner = 1
        ORDER BY e.year DESC, cat.name ASC
        LIMIT 1
    ');
    $stmt->execute([':slug' => $ceremonySlug]);
    $latestWinner = $stmt->fetch() ?: null;
    if ($latestWinner) $latestWinner['year'] = (int)$latestWinner['year'];

    return [
        'most_decorated_film' => $mostDecoratedFilm,
        'most_total_wins_film' => $mostTotalWinsFilm,
        'most_decorated_person' => $mostDecoratedPerson,
        'longest_streak' => null,
        'first_edition_winner' => $firstEditionWinner,
        'latest_winner' => $latestWinner,
        'total_films_honoured' => $totalFilmsHonoured
    ];
}

function getEditionYearPreview($ceremonySlug, $year) {
    $ceremonySlug = resolveSlug($ceremonySlug);
    $pdo = DB::connection();
    
    // 1. Get edition details
    $stmt = $pdo->prepare('
        SELECT e.id AS edition_id, e.year, e.venue, e.host
        FROM editions e
        JOIN ceremonies c ON e.ceremony_id = c.id
        WHERE c.slug = :slug AND e.year = :year
        LIMIT 1
    ');
    $stmt->execute([':slug' => $ceremonySlug, ':year' => (int)$year]);
    $ed = $stmt->fetch();
    if (!$ed) return null;

    $editionId = (int)$ed['edition_id'];

    // 2. Counts
    $stmt = $pdo->prepare('
        SELECT COUNT(DISTINCT category_id) AS total_categories,
               SUM(CASE WHEN is_winner = 1 THEN 1 ELSE 0 END) AS total_winners
        FROM nominations
        WHERE edition_id = :eid
    ');
    $stmt->execute([':eid' => $editionId]);
    $counts = $stmt->fetch();

    // 3. Top 5 winners
    $stmt = $pdo->prepare('
        SELECT cat.name AS category_name, n.nominee_text AS winner_text,
               f.title AS film_title, p.name AS person_name
        FROM nominations n
        JOIN categories cat ON n.category_id = cat.id
        LEFT JOIN films f ON n.film_id = f.id
        LEFT JOIN persons p ON n.person_id = p.id
        WHERE n.edition_id = :eid AND n.is_winner = 1
        ORDER BY cat.department ASC, cat.name ASC
        LIMIT 5
    ');
    $stmt->execute([':eid' => $editionId]);
    $topWinners = $stmt->fetchAll();

    return [
        'year' => (int)$ed['year'],
        'venue' => $ed['venue'],
        'host' => $ed['host'],
        'total_categories' => (int)($counts['total_categories'] ?? 0),
        'total_winners' => (int)($counts['total_winners'] ?? 0),
        'top_winners' => array_map(fn($w) => [
            'category_name' => $w['category_name'],
            'winner_text' => $w['winner_text'],
            'film_title' => $w['film_title'] ?: null,
            'person_name' => $w['person_name'] ?: null
        ], $topWinners)
    ];
}

function searchCeremonyArchive($ceremonySlug, $query) {
    $ceremonySlug = resolveSlug($ceremonySlug);
    $pdo = DB::connection();
    $like = '%' . $query . '%';

    $stmt = $pdo->prepare('
        SELECT e.year, cat.name AS categoryName, n.nominee_text AS winnerName,
               f.title AS filmTitle, p.name AS personName
        FROM nominations n
        JOIN editions e ON n.edition_id = e.id
        JOIN ceremonies c ON e.ceremony_id = c.id
        JOIN categories cat ON n.category_id = cat.id
        LEFT JOIN films f ON n.film_id = f.id
        LEFT JOIN persons p ON n.person_id = p.id
        WHERE c.slug = :slug
          AND (n.nominee_text LIKE :q OR f.title LIKE :q OR p.name LIKE :q)
        ORDER BY e.year DESC
        LIMIT 100
    ');
    $stmt->execute([':slug' => $ceremonySlug, ':q' => $like]);
    $rows = $stmt->fetchAll();

    return array_map(fn($r) => array_merge($r, ['year' => (int)$r['year']]), $rows);
}

function parseSearchIntent($query) {
    $q = ' ' . strtolower(trim($query)) . ' ';
    
    // Stop words to remove (surrounded by spaces to ensure exact word matches)
    $stopWords = [
        ' for which ', ' which ', ' the ', ' in ', ' did ', ' what ', ' where ', ' when ', 
        ' who ', ' of ', ' to ', ' a ', ' an ', ' she ', ' he ', ' movies ', ' movie ', 
        ' films ', ' film ', ' picture ', ' pictures ', ' actors ', ' actor ', 
        ' actress ', ' director ', ' directors '
    ];
    foreach ($stopWords as $sw) {
        $q = str_replace($sw, ' ', $q);
    }
    
    $intent = [
        'return_type' => 'all', // films, persons, ceremonies
        'condition' => null, // 'winner', 'nominated'
        'keyword' => ''
    ];
    
    // Detect return type
    if (preg_match('/\b(movie|movies|film|films|picture|pictures|nomination|nominations)\b/i', $query)) {
        $intent['return_type'] = 'films';
    } elseif (preg_match('/\b(actor|actress|director|person|people)\b/i', $query)) {
        $intent['return_type'] = 'persons';
    }
    
    // Detect condition
    if (preg_match('/\b(won|winner|winning|got award|awarded|award|awards)\b/i', $query)) {
        $intent['condition'] = 'winner';
    } elseif (preg_match('/\b(nominated|nomination|nominee|nominations)\b/i', $query)) {
        $intent['condition'] = 'nominated';
    }
    
    // Clean up intent keywords from the search text to isolate the core entity name
    $intentKeywords = [
        ' won ', ' winner ', ' winning ', ' got award ', ' awarded ', ' award ', ' awards ',
        ' nominated ', ' nomination ', ' nominee ', ' nominations '
    ];
    foreach ($intentKeywords as $ik) {
        $q = str_replace($ik, ' ', $q);
    }
    
    $intent['keyword'] = trim(preg_replace('/\s+/', ' ', $q));
    
    if (strlen($intent['keyword']) >= 2) {
        return $intent;
    }
    
    return null;
}

function searchAll($query, $limit = 5, $offset = 0, $type = 'all') {
    $cleanQuery = trim($query);
    if (empty($cleanQuery)) {
        return ['films' => [], 'persons' => [], 'ceremonies' => [], 'results' => []];
    }

    $pdo = DB::connection();

    // Parse year if present in query
    $queryYear = null;
    if (preg_match('/\b(19\d{2}|20\d{2})\b/', $cleanQuery, $matches)) {
        $queryYear = (int)$matches[1];
        $cleanQueryNoYear = trim(str_replace($matches[1], '', $cleanQuery));
        if (strlen($cleanQueryNoYear) < 2) {
            $cleanQueryNoYear = $cleanQuery;
        }
    } else {
        $cleanQueryNoYear = $cleanQuery;
    }

    // 1. Intent Parsing
    $intent = parseSearchIntent($cleanQueryNoYear);
    $is_winner = null;
    $entityKeyword = $cleanQueryNoYear;
    
    if ($intent) {
        if ($intent['condition'] === 'winner') {
            $is_winner = 1;
        } elseif ($intent['condition'] === 'nominated') {
            $is_winner = 0;
        }
        $entityKeyword = $intent['keyword'];
    }

    $likeKeyword = '%' . $entityKeyword . '%';

    // 2. Dynamic MySQL Query Construction
    $filmsRes = [];
    $personsRes = [];
    $ceremoniesRes = [];

    // Search films
    if ($type === 'all' || $type === 'films') {
        $matchedFilmIds = [];
        
        // A. Match film title directly
        $stmt = $pdo->prepare('SELECT id FROM films WHERE title LIKE :kw LIMIT 200');
        $stmt->bindValue(':kw', $likeKeyword);
        $stmt->execute();
        $matchedFilmIds = array_merge($matchedFilmIds, $stmt->fetchAll(PDO::FETCH_COLUMN));

        // B. Match person name (two-step)
        $stmt = $pdo->prepare('SELECT id FROM persons WHERE name LIKE :kw LIMIT 100');
        $stmt->bindValue(':kw', $likeKeyword);
        $stmt->execute();
        $personIds = $stmt->fetchAll(PDO::FETCH_COLUMN);
        if (!empty($personIds)) {
            $placeholders = implode(',', array_fill(0, count($personIds), '?'));
            $stmt = $pdo->prepare("SELECT DISTINCT film_id FROM nominations WHERE person_id IN ($placeholders) LIMIT 200");
            $stmt->execute($personIds);
            $matchedFilmIds = array_merge($matchedFilmIds, array_filter($stmt->fetchAll(PDO::FETCH_COLUMN)));
        }

        // C. Match nominee text
        $stmt = $pdo->prepare('SELECT DISTINCT film_id FROM nominations WHERE nominee_text LIKE :kw LIMIT 200');
        $stmt->bindValue(':kw', $likeKeyword);
        $stmt->execute();
        $matchedFilmIds = array_merge($matchedFilmIds, array_filter($stmt->fetchAll(PDO::FETCH_COLUMN)));

        // D. Match category name (two-step)
        $stmt = $pdo->prepare('SELECT id FROM categories WHERE name LIKE :kw LIMIT 100');
        $stmt->bindValue(':kw', $likeKeyword);
        $stmt->execute();
        $catIds = $stmt->fetchAll(PDO::FETCH_COLUMN);
        if (!empty($catIds)) {
            $placeholders = implode(',', array_fill(0, count($catIds), '?'));
            $stmt = $pdo->prepare("SELECT DISTINCT film_id FROM nominations WHERE category_id IN ($placeholders) LIMIT 200");
            $stmt->execute($catIds);
            $matchedFilmIds = array_merge($matchedFilmIds, array_filter($stmt->fetchAll(PDO::FETCH_COLUMN)));
        }

        $matchedFilmIds = array_unique($matchedFilmIds);

        if (!empty($matchedFilmIds)) {
            $placeholders = implode(',', array_fill(0, count($matchedFilmIds), '?'));
            $sql = "
                SELECT DISTINCT f.id, f.slug, f.title, f.year, f.poster_url AS posterUrl,
                                c.name AS category_name, cer.name AS ceremony_name, e.year AS edition_year
                FROM films f
                LEFT JOIN nominations n ON n.film_id = f.id
                LEFT JOIN categories c ON n.category_id = c.id
                LEFT JOIN editions e ON n.edition_id = e.id
                LEFT JOIN ceremonies cer ON e.ceremony_id = cer.id
                WHERE f.id IN ($placeholders)
            ";
            if ($is_winner === 1) {
                $sql .= ' AND n.is_winner = 1 ';
            }
            if ($queryYear !== null) {
                $sql .= ' AND f.year = ? ';
            }
            $sql .= ' LIMIT ? OFFSET ?';

            $stmt = $pdo->prepare($sql);
            $paramIdx = 1;
            foreach ($matchedFilmIds as $id) {
                $stmt->bindValue($paramIdx++, $id, PDO::PARAM_INT);
            }
            if ($queryYear !== null) {
                $stmt->bindValue($paramIdx++, $queryYear, PDO::PARAM_INT);
            }
            $stmt->bindValue($paramIdx++, $limit, PDO::PARAM_INT);
            $stmt->bindValue($paramIdx++, $offset, PDO::PARAM_INT);
            $stmt->execute();
            $filmsRes = $stmt->fetchAll();
        } else {
            $filmsRes = [];
        }

        // 3. Typo Tolerance & Fallback (Fuzzy Matching)
        // Fallback 1 (SOUNDEX matching) has been disabled to prevent database performance issues.

        if (count($filmsRes) === 0) {
            // Fallback 2: Split-word matching loop (for partial typo tolerance)
            $words = array_values(array_filter(explode(' ', $entityKeyword)));
            if (count($words) > 0) {
                $matchedFilmIds = [];
                
                // Film titles matching all words
                $titleConds = [];
                foreach ($words as $idx => $w) {
                    $titleConds[] = "title LIKE :w{$idx}";
                }
                $stmt = $pdo->prepare('SELECT id FROM films WHERE ' . implode(' AND ', $titleConds) . ' LIMIT 200');
                foreach ($words as $idx => $w) {
                    $stmt->bindValue(":w{$idx}", '%' . $w . '%');
                }
                $stmt->execute();
                $matchedFilmIds = array_merge($matchedFilmIds, $stmt->fetchAll(PDO::FETCH_COLUMN));

                // Person name matching all words (two-step)
                $personConds = [];
                foreach ($words as $idx => $w) {
                    $personConds[] = "name LIKE :w{$idx}";
                }
                $stmt = $pdo->prepare('SELECT id FROM persons WHERE ' . implode(' AND ', $personConds) . ' LIMIT 100');
                foreach ($words as $idx => $w) {
                    $stmt->bindValue(":w{$idx}", '%' . $w . '%');
                }
                $stmt->execute();
                $personIds = $stmt->fetchAll(PDO::FETCH_COLUMN);
                if (!empty($personIds)) {
                    $placeholders = implode(',', array_fill(0, count($personIds), '?'));
                    $stmt = $pdo->prepare("SELECT DISTINCT film_id FROM nominations WHERE person_id IN ($placeholders) LIMIT 200");
                    $stmt->execute($personIds);
                    $matchedFilmIds = array_merge($matchedFilmIds, array_filter($stmt->fetchAll(PDO::FETCH_COLUMN)));
                }
                
                $matchedFilmIds = array_unique($matchedFilmIds);

                if (!empty($matchedFilmIds)) {
                    $placeholders = implode(',', array_fill(0, count($matchedFilmIds), '?'));
                    $sqlSplit = "
                        SELECT DISTINCT f.id, f.slug, f.title, f.year, f.poster_url AS posterUrl,
                                        c.name AS category_name, cer.name AS ceremony_name, e.year AS edition_year
                        FROM films f
                        LEFT JOIN nominations n ON n.film_id = f.id
                        LEFT JOIN categories c ON n.category_id = c.id
                        LEFT JOIN editions e ON n.edition_id = e.id
                        LEFT JOIN ceremonies cer ON e.ceremony_id = cer.id
                        WHERE f.id IN ($placeholders)
                    ";
                    if ($is_winner === 1) {
                        $sqlSplit .= ' AND n.is_winner = 1 ';
                    }
                    if ($queryYear !== null) {
                        $sqlSplit .= ' AND f.year = ? ';
                    }
                    $sqlSplit .= ' LIMIT ? OFFSET ?';

                    $stmt = $pdo->prepare($sqlSplit);
                    $paramIdx = 1;
                    foreach ($matchedFilmIds as $id) {
                        $stmt->bindValue($paramIdx++, $id, PDO::PARAM_INT);
                    }
                    if ($queryYear !== null) {
                        $stmt->bindValue($paramIdx++, $queryYear, PDO::PARAM_INT);
                    }
                    $stmt->bindValue($paramIdx++, $limit, PDO::PARAM_INT);
                    $stmt->bindValue($paramIdx++, $offset, PDO::PARAM_INT);
                    $stmt->execute();
                    $filmsRes = $stmt->fetchAll();
                }
            }
        }
    }

    // Search persons
    if ($type === 'all' || $type === 'persons') {
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
        $personsRes = $stmt->fetchAll();

        // SOUNDEX fallback for persons has been disabled to prevent performance issues.
    }

    // Search ceremonies
    if ($type === 'all') {
        global $NAV_DATA;
        $ceremoniesRes = [];
        $words = array_filter(explode(' ', strtolower($entityKeyword)));
        
        foreach ($NAV_DATA as $cat) {
            foreach ($cat['industries'] as $ind) {
                foreach ($ind['ceremonies'] as $c) {
                    $targetStr = strtolower($c['name'] . ' ' . $c['slug']);
                    $matchesAll = true;
                    foreach ($words as $w) {
                        if (strpos($targetStr, $w) === false) {
                            $matchesAll = false;
                            break;
                        }
                    }
                    if ($matchesAll) {
                        $ceremoniesRes[] = [
                            'id' => rand(999000, 999999),
                            'slug' => $c['slug'],
                            'name' => $c['name'],
                            'country' => $c['country']
                        ];
                    }
                }
            }
        }
        
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
        $dbCers = $stmt->fetchAll();
        
        $seen = [];
        $merged = [];
        foreach ($ceremoniesRes as $c) {
            if (!in_array($c['slug'], $seen)) {
                $seen[] = $c['slug'];
                $merged[] = $c;
            }
        }
        foreach ($dbCers as $c) {
            if (!in_array($c['slug'], $seen)) {
                $seen[] = $c['slug'];
                $merged[] = $c;
            }
        }
        $ceremoniesRes = array_slice($merged, 0, $limit);
    }

    // Build universal search output results
    $results = [];
    foreach ($filmsRes as $f) {
        $subtitle = $f['year'] ? 'Film · ' . $f['year'] : 'Film';
        if (!empty($f['category_name']) && !empty($f['ceremony_name'])) {
            $subtitle = $f['category_name'] . ' (' . $f['ceremony_name'] . ' ' . ($f['edition_year'] ?? $f['year']) . ')';
        }
        $results[] = [
            'type' => 'film',
            'title' => $f['title'],
            'subtitle' => $subtitle,
            'url' => '/films/' . $f['slug'],
        ];
    }
    foreach ($personsRes as $p) {
        $results[] = [
            'type' => 'person',
            'title' => $p['name'],
            'subtitle' => 'Person',
            'url' => '/persons/' . $p['slug'],
        ];
    }
    foreach ($ceremoniesRes as $c) {
        $results[] = [
            'type' => 'ceremony',
            'title' => $c['name'],
            'subtitle' => 'Ceremony · ' . ($c['country'] ?? ''),
            'url' => '/cinema/' . $c['slug'],
        ];
    }

    // Human-friendly intent message (e.g. "Here are movies where Alia Bhatt won...")
    $intentMessage = "";
    if ($intent) {
        $kwTitle = ucwords($entityKeyword);
        if ($is_winner === 1) {
            $intentMessage = "Here are the awards won by \"{$kwTitle}\":";
        } elseif ($is_winner === 0) {
            $intentMessage = "Here are the nominations received by \"{$kwTitle}\":";
        } else {
            $intentMessage = "Here are results matching \"{$kwTitle}\":";
        }
    }

    return [
        'films' => $filmsRes,
        'persons' => $personsRes,
        'ceremonies' => $ceremoniesRes,
        'intent_message' => $intentMessage,
        'results' => $results
    ];
}

function getCategoryAllWinners($ceremonySlug, $categorySlug) {
    $ceremonySlug = resolveSlug($ceremonySlug);
    $pdo = DB::connection();
    
    // Get ceremony and category info
    $stmt = $pdo->prepare('
        SELECT c.id AS ceremonyId, c.name AS ceremonyName, c.slug AS ceremonySlug,
               cat.id AS categoryId, cat.name AS categoryName, cat.department AS categoryDepartment
        FROM ceremonies c
        JOIN categories cat ON cat.slug = ?
        WHERE c.slug = ?
        LIMIT 1
    ');
    $stmt->execute([$categorySlug, $ceremonySlug]);
    $meta = $stmt->fetch();
    
    if (!$meta) return null;
    
    // Get winners
    $stmt = $pdo->prepare('
        SELECT e.year, n.nominee_text, 
               p.name AS personName, p.slug AS personSlug,
               f.title AS filmTitle, f.slug AS filmSlug
        FROM nominations n
        JOIN editions e ON n.edition_id = e.id
        LEFT JOIN persons p ON n.person_id = p.id
        LEFT JOIN films f ON n.film_id = f.id
        WHERE n.category_id = ? AND e.ceremony_id = ? AND n.is_winner = 1
        ORDER BY e.year DESC
    ');
    $stmt->execute([$meta['categoryId'], $meta['ceremonyId']]);
    $winnersRaw = $stmt->fetchAll();
    
    $winners = [];
    foreach ($winnersRaw as $w) {
        $winners[] = [
            'year' => (int)$w['year'],
            'nominee_text' => $w['nominee_text'],
            'person' => $w['personName'] ? ['name' => $w['personName'], 'slug' => $w['personSlug']] : null,
            'film' => $w['filmTitle'] ? ['title' => $w['filmTitle'], 'slug' => $w['filmSlug']] : null
        ];
    }
    
    return [
        'ceremony' => [
            'name' => $meta['ceremonyName']
        ],
        'category' => [
            'name' => $meta['categoryName'],
            'department' => $meta['categoryDepartment'] ?: 'General'
        ],
        'winners' => $winners
    ];
}
