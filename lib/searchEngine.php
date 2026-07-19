<?php
// lib/searchEngine.php
require_once __DIR__ . '/../config/DB.php';
require_once __DIR__ . '/queryParser.php';

class SearchEngine {
    public static function search($queryRaw, $limit = 50, $offset = 0) {
        $parsed = parseQuery($queryRaw);
        $pdo = DB::connection();

        $films = [];
        $persons = [];
        $ceremonies = [];

        // Rule A5: leftover search text must confidently resolve to a known entity
        if (!empty($parsed['leftoverText'])) {
            return [
                'films' => [],
                'persons' => [],
                'ceremonies' => [],
                'intent_message' => null
            ];
        }

        // Build dynamic WHERE clause
        $where = [];
        $params = [];

        if ($parsed['person']) {
            $where[] = "(n.person_id = :person_id OR n.nominee_text LIKE :person_name)";
            $params[':person_id'] = $parsed['person']['id'];
            $params[':person_name'] = '%' . $parsed['person']['name'] . '%';
        }

        if ($parsed['film']) {
            $where[] = "n.film_id = :film_id";
            $params[':film_id'] = $parsed['film']['id'];
        }

        if ($parsed['ceremony']) {
            $where[] = "e.ceremony_id = :ceremony_id";
            $params[':ceremony_id'] = $parsed['ceremony']['id'];
        }

        if ($parsed['category']) {
            $where[] = "c.name LIKE :category";
            $params[':category'] = '%' . $parsed['category'] . '%';
        }

        if ($parsed['year']) {
            $where[] = "e.year = :year";
            $params[':year'] = $parsed['year'];
        }

        if ($parsed['yearRange']) {
            $where[] = "e.year BETWEEN :year_start AND :year_end";
            $params[':year_start'] = $parsed['yearRange'][0];
            $params[':year_end'] = $parsed['yearRange'][1];
        }

        if ($parsed['onlyWinners'] !== null) {
            $where[] = "n.is_winner = :is_winner";
            $params[':is_winner'] = $parsed['onlyWinners'] ? 1 : 0;
        }

        if ($parsed['ceremony']) {
            $stmt = $pdo->prepare("SELECT id, name, slug FROM ceremonies WHERE id = :id");
            $stmt->execute([':id' => $parsed['ceremony']['id']]);
            $ceremonies = $stmt->fetchAll(PDO::FETCH_ASSOC);
        }

        // Build and execute dynamic query over nominations
        $nominations = [];
        if (!empty($where)) {
            $whereClause = "WHERE " . implode(" AND ", $where);
            $sql = "
                SELECT DISTINCT 
                    f.id AS film_id, f.title AS film_title, f.slug AS film_slug, f.year AS film_year, f.poster_url AS film_poster,
                    p.id AS person_id, p.name AS person_name, p.slug AS person_slug, p.photo_url AS person_photo,
                    c.name AS category_name, cer.name AS ceremony_name, cer.slug AS ceremony_slug, e.year AS edition_year, e.slug AS edition_slug,
                    n.is_winner, n.nominee_text AS nominee_name
                FROM nominations n
                LEFT JOIN films f ON n.film_id = f.id
                LEFT JOIN persons p ON n.person_id = p.id
                LEFT JOIN categories c ON n.category_id = c.id
                LEFT JOIN editions e ON n.edition_id = e.id
                LEFT JOIN ceremonies cer ON e.ceremony_id = cer.id
                $whereClause
                ORDER BY 
                    (CASE WHEN n.is_winner = 1 THEN 1 ELSE 0 END) DESC,
                    e.year DESC
                LIMIT :limit OFFSET :offset
            ";

            $stmt = $pdo->prepare($sql);
            foreach ($params as $k => $v) {
                $stmt->bindValue($k, $v);
            }
            $stmt->bindValue(':limit', (int)$limit, PDO::PARAM_INT);
            $stmt->bindValue(':offset', (int)$offset, PDO::PARAM_INT);
            $stmt->execute();
            $nominations = $stmt->fetchAll(PDO::FETCH_ASSOC);
        }

        $aliases = SearchAliases::getAliases();

        // Populate films and persons
        foreach ($nominations as $nom) {
            if ($nom['film_id']) {
                $nomineeName = $nom['nominee_name'] ?: $nom['film_title'];
                $nomineeLower = strtolower(trim($nomineeName));
                $nomineeUrl = '#';

                if (isset($aliases['persons'][$nomineeLower]) && !empty($aliases['persons'][$nomineeLower]['slug'])) {
                    $nomineeUrl = '/persons/' . $aliases['persons'][$nomineeLower]['slug'];
                } else {
                    foreach ($aliases['films'] as $f) {
                        if (strtolower($f['title']) === $nomineeLower) {
                            $nomineeUrl = '/films/' . $f['slug'];
                            break;
                        }
                    }
                }

                $films[] = [
                    'id' => $nom['film_id'],
                    'title' => $nomineeName,
                    'slug' => $nom['film_slug'],
                    'year' => $nom['film_year'],
                    'posterUrl' => $nom['film_poster'],
                    'category_name' => $nom['category_name'],
                    'ceremony_name' => $nom['ceremony_name'],
                    'ceremony_slug' => $nom['ceremony_slug'],
                    'edition_year' => $nom['edition_year'],
                    'edition_slug' => $nom['edition_slug'],
                    'nominee_url' => $nomineeUrl
                ];
            }
            if ($nom['person_id']) {
                $persons[$nom['person_id']] = [
                    'id' => $nom['person_id'],
                    'name' => $nom['person_name'],
                    'slug' => $nom['person_slug'],
                    'photoUrl' => $nom['person_photo']
                ];
            }
        }

        return [
            'films' => array_values($films),
            'persons' => array_values($persons),
            'ceremonies' => array_values($ceremonies),
            'intent_message' => null
        ];
    }
}
