<?php
// lib/searchAliases.php
require_once __DIR__ . '/../config/DB.php';

class SearchAliases {
    private static $cacheFile = __DIR__ . '/../cache/search_dictionary.cache.php';

    public static function getAliases() {
        if (file_exists(self::$cacheFile)) {
            return include self::$cacheFile;
        }
        return self::rebuildCache();
    }

    public static function rebuildCache() {
        $pdo = DB::connection();

        // Fetch all films to build a fast title index and lookup map
        $films = $pdo->query("SELECT id, title, slug, year FROM films")->fetchAll(PDO::FETCH_ASSOC);
        $filmTitles = [];
        $filmIndex = [];
        foreach ($films as $f) {
            $titleLower = strtolower(trim($f['title']));
            $filmTitles[$titleLower] = true;
            $filmIndex[] = [
                'id' => (int)$f['id'],
                'title' => $f['title'],
                'slug' => $f['slug'],
                'year' => (int)$f['year']
            ];
        }

        // Fetch ceremonies and build ceremony aliases
        $ceremonies = $pdo->query("SELECT id, name, short_name, slug FROM ceremonies")->fetchAll(PDO::FETCH_ASSOC);
        $ceremonyAliases = [];
        $ceremonyNames = [];
        foreach ($ceremonies as $c) {
            $id = (int)$c['id'];
            $fullName = strtolower(trim($c['name']));
            $shortName = strtolower(trim($c['short_name'] ?? ''));
            $slug = $c['slug'];

            $ceremonyNames[] = $fullName;

            $data = ['id' => $id, 'name' => $c['name'], 'slug' => $slug];

            $ceremonyAliases[$fullName] = $data;
            if ($shortName) {
                $ceremonyAliases[$shortName] = $data;
                $ceremonyNames[] = $shortName;
            }

            // Add standard abbreviations
            if (strpos($fullName, 'filmfare') !== false) {
                $ceremonyAliases['filmfare'] = $data;
            }
            if (strpos($fullName, 'academy awards') !== false || strpos($fullName, 'oscar') !== false) {
                $ceremonyAliases['oscars'] = $data;
                $ceremonyAliases['oscar'] = $data;
            }
            if ($slug === 'bafta-awards') {
                $ceremonyAliases['bafta'] = $data;
            }
        }

        // Build person aliases
        $personAliases = [];
        $addPerson = function($name, $id, $slug = null) use (&$personAliases) {
            $fullNameLower = strtolower(trim($name));
            if (empty($fullNameLower)) return;

            $data = [
                'id' => (int)$id,
                'name' => trim($name),
                'slug' => $slug
            ];

            if (!isset($personAliases[$fullNameLower])) {
                $personAliases[$fullNameLower] = $data;
            }

        };

        // 1. Fetch from persons table
        $persons = $pdo->query("SELECT id, name, slug FROM persons")->fetchAll(PDO::FETCH_ASSOC);
        foreach ($persons as $p) {
            $addPerson($p['name'], $p['id'], $p['slug']);
        }

        // Fetch distinct nominee_text values that are associated with person categories
        $personNomineesQuery = $pdo->query("
            SELECT DISTINCT n.nominee_text 
            FROM nominations n
            JOIN categories c ON n.category_id = c.id
            WHERE c.name LIKE '%actor%' 
               OR c.name LIKE '%actress%' 
               OR c.name LIKE '%director%' 
               OR c.name LIKE '%screenplay%'
               OR c.name LIKE '%editor%'
               OR c.name LIKE '%music%'
               OR c.name LIKE '%singer%'
               OR c.name LIKE '%lyricist%'
               OR c.name LIKE '%helmer%'
               OR c.name LIKE '%writer%'
               OR c.name LIKE '%cinematography%'
               OR c.name LIKE '%cinematographer%'
        ");
        $personNomineeNames = [];
        while ($pName = $personNomineesQuery->fetchColumn()) {
            $personNomineeNames[strtolower(trim($pName))] = true;
        }

        // 2. Fetch distinct nominee_text from nominations (excludes films and ceremonies unless they are person nominees)
        $nominees = $pdo->query("SELECT DISTINCT nominee_text, person_id FROM nominations")->fetchAll(PDO::FETCH_ASSOC);
        foreach ($nominees as $nom) {
            $name = trim($nom['nominee_text']);
            $nameLower = strtolower($name);
            $isPersonNominee = isset($personNomineeNames[$nameLower]);
            if (empty($name) || (isset($filmTitles[$nameLower]) && !$isPersonNominee) || in_array($nameLower, $ceremonyNames)) {
                continue;
            }
            $addPerson($name, $nom['person_id'], null);
        }

        // 3. Add top star nicknames
        $nicknames = [
            'srk' => 'Shah Rukh Khan',
            'king khan' => 'Shah Rukh Khan',
            'big b' => 'Amitabh Bachchan',
            'bhai' => 'Salman Khan',
            'mr perfectionist' => 'Aamir Khan',
            'aamir' => 'Aamir Khan',
            'alia' => 'Alia Bhatt'
        ];
        foreach ($nicknames as $nick => $realName) {
            $realLower = strtolower($realName);
            if (isset($personAliases[$realLower])) {
                $personAliases[$nick] = $personAliases[$realLower];
            }
        }

        $dataToCache = [
            'persons' => $personAliases,
            'ceremonies' => $ceremonyAliases,
            'films' => $filmIndex
        ];

        // Ensure cache dir exists
        $cacheDir = dirname(self::$cacheFile);
        if (!is_dir($cacheDir)) {
            mkdir($cacheDir, 0755, true);
        }

        // Write to file as PHP array
        $content = "<?php\nreturn " . var_export($dataToCache, true) . ";\n";
        file_put_contents(self::$cacheFile, $content);

        return $dataToCache;
    }
}
