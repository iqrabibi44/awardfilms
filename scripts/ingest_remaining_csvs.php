<?php
/**
 * Ingest remaining film awards CSV datasets into the MySQL database.
 * Run from project root: C:\xampp\php\php.exe scripts/ingest_remaining_csvs.php
 */

require_once __DIR__ . '/../config/DB.php';

// Disable memory limit and time limit for large imports
ini_set('memory_limit', '-1');
set_time_limit(0);

$pdo = DB::connection();

function makeSlug(string $text): string {
    $text = preg_replace('~[^\pL\d]+~u', '-', $text);
    if (function_exists('iconv')) {
        $text = iconv('utf-8', 'us-ascii//TRANSLIT', $text);
    }
    $text = preg_replace('~[^-\w]+~', '', $text);
    $text = trim($text, '-');
    $text = preg_replace('~-+~', '-', $text);
    $text = strtolower($text);
    return empty($text) ? 'n-a' : substr($text, 0, 255);
}

function parseCsv(string $filePath): array {
    if (!file_exists($filePath) || ($handle = fopen($filePath, "r")) === false) {
        return [];
    }
    $headers = fgetcsv($handle);
    if (!$headers) {
        fclose($handle);
        return [];
    }
    $cleanHeaders = array_map(function($h) {
        $h = preg_replace('/^[\xEF\xBB\xBF\xFF\xFE]/', '', $h);
        return strtolower(trim(str_replace([' ', '_', '-'], '', $h)));
    }, $headers);
    
    $rows = [];
    while (($row = fgetcsv($handle)) !== false) {
        if (count($row) < count($headers)) {
            $row = array_pad($row, count($headers), '');
        }
        $rowData = array_combine($cleanHeaders, array_slice($row, 0, count($headers)));
        $rows[] = $rowData;
    }
    fclose($handle);
    return $rows;
}

function ensureCeremony($pdo, string $name, string $country = 'Global', ?string $customSlug = null): array {
    $slug = $customSlug ?: makeSlug($name);
    if ($slug === 'pisa-awards') $slug = 'pisa';
    if ($slug === 'bafta') $slug = 'bafta-film-awards';
    
    $stmt = $pdo->prepare("SELECT id, slug FROM ceremonies WHERE slug = ? LIMIT 1");
    $stmt->execute([$slug]);
    $res = $stmt->fetch();
    if ($res) {
        return $res;
    }
    $ins = $pdo->prepare("INSERT INTO ceremonies (slug, name, country) VALUES (?, ?, ?)");
    $ins->execute([$slug, $name, $country]);
    return ['id' => $pdo->lastInsertId(), 'slug' => $slug];
}

function ensureEdition($pdo, int $ceremonyId, int $year, string $ceremonySlug): int {
    $stmt = $pdo->prepare("SELECT id FROM editions WHERE ceremony_id = ? AND year = ? LIMIT 1");
    $stmt->execute([$ceremonyId, $year]);
    $res = $stmt->fetch();
    if ($res) {
        return (int)$res['id'];
    }
    $slug = $ceremonySlug . '-' . $year;
    // Check uniqueness
    $check = $pdo->prepare("SELECT id FROM editions WHERE slug = ?");
    $check->execute([$slug]);
    if ($check->fetch()) {
        $slug .= '-' . uniqid();
    }
    $ins = $pdo->prepare("INSERT INTO editions (ceremony_id, year, slug) VALUES (?, ?, ?)");
    $ins->execute([$ceremonyId, $year, $slug]);
    return (int)$pdo->lastInsertId();
}

function ensureCategory($pdo, int $ceremonyId, string $name): int {
    $slug = substr(makeSlug($name), 0, 180);
    $stmt = $pdo->prepare("SELECT id FROM categories WHERE ceremony_id = ? AND slug = ? LIMIT 1");
    $stmt->execute([$ceremonyId, $slug]);
    $res = $stmt->fetch();
    if ($res) {
        return (int)$res['id'];
    }
    // Check if the slug exists (with a different name) to avoid duplicate entry violation
    $check = $pdo->prepare("SELECT id FROM categories WHERE ceremony_id = ? AND slug = ?");
    $check->execute([$ceremonyId, $slug]);
    if ($check->fetch()) {
        $slug = substr($slug, 0, 160) . '-' . uniqid();
    }
    $ins = $pdo->prepare("INSERT INTO categories (ceremony_id, name, slug, department) VALUES (?, ?, ?, 'General')");
    $ins->execute([$ceremonyId, $name, $slug]);
    return (int)$pdo->lastInsertId();
}

function ensureFilm($pdo, string $title, int $year, string $country = 'Global', string $language = 'English'): int {
    $title = trim($title);
    if (empty($title)) return 0;
    
    $stmt = $pdo->prepare("SELECT id FROM films WHERE title = ? LIMIT 1");
    $stmt->execute([$title]);
    $res = $stmt->fetch();
    if ($res) {
        return (int)$res['id'];
    }
    $slug = makeSlug($title . ' ' . $year);
    // Check uniqueness
    $check = $pdo->prepare("SELECT id FROM films WHERE slug = ?");
    $check->execute([$slug]);
    if ($check->fetch()) {
        $slug .= '-' . uniqid();
    }
    $ins = $pdo->prepare("INSERT INTO films (slug, title, year, country, language) VALUES (?, ?, ?, ?, ?)");
    $ins->execute([$slug, $title, $year, $country, $language]);
    return (int)$pdo->lastInsertId();
}

function ensurePerson($pdo, string $name): int {
    $name = trim($name);
    if (empty($name)) return 0;
    
    $stmt = $pdo->prepare("SELECT id FROM persons WHERE name = ? LIMIT 1");
    $stmt->execute([$name]);
    $res = $stmt->fetch();
    if ($res) {
        return (int)$res['id'];
    }
    $slug = makeSlug($name);
    $check = $pdo->prepare("SELECT id FROM persons WHERE slug = ?");
    $check->execute([$slug]);
    if ($check->fetch()) {
        $slug .= '-' . uniqid();
    }
    $ins = $pdo->prepare("INSERT INTO persons (slug, name) VALUES (?, ?)");
    $ins->execute([$slug, $name]);
    return (int)$pdo->lastInsertId();
}

function insertNomination($pdo, int $editionId, int $categoryId, int $filmId, int $personId, string $nomineeText, int $isWinner, ?string $sourceRef) {
    $ins = $pdo->prepare("
        INSERT INTO nominations (edition_id, category_id, film_id, person_id, nominee_text, is_winner, source_ref) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON DUPLICATE KEY UPDATE 
            is_winner = VALUES(is_winner),
            source_ref = COALESCE(VALUES(source_ref), source_ref)
    ");
    $pId = $personId > 0 ? $personId : null;
    $fId = $filmId > 0 ? $filmId : null;
    $ins->execute([$editionId, $categoryId, $fId, $pId, $nomineeText, $isWinner, $sourceRef]);
}

function parse_raw_csv_name(string $filePath): array {
    $basename = basename($filePath, '.csv');
    if (strpos($basename, '--') !== false) {
        $parts = explode('--', $basename, 2);
        $ceremony_slug = $parts[0];
        $category_slug = $parts[1];
        $ceremony_name = ucwords(str_replace('-', ' ', $ceremony_slug));
        $category_name = ucwords(str_replace('-', ' ', $category_slug));
        return [$ceremony_name, $category_name];
    }
    return [ucwords(str_replace('-', ' ', $basename)), 'General'];
}

// ==========================================
// ROUTINE 1: Standard Raw CSVs (scripts/data/raw/*.csv)
// ==========================================
echo "=== ROUTINE 1: Importing scripts/data/raw/*.csv ===\n";
$rawDir = __DIR__ . '/data/raw';
if (is_dir($rawDir)) {
    $files = glob($rawDir . '/*.csv');
    $skipPatterns = ['_raw.csv', 'the_oscar_award.csv'];
    
    foreach ($files as $filePath) {
        $skip = false;
        foreach ($skipPatterns as $pattern) {
            if (strpos(basename($filePath), $pattern) !== false) {
                $skip = true;
                break;
            }
        }
        if ($skip) continue;
        
        echo "Processing " . basename($filePath) . "... ";
        $rows = parseCsv($filePath);
        if (empty($rows)) {
            echo "Empty or error.\n";
            continue;
        }
        
        list($ceremonyName, $categoryName) = parse_raw_csv_name($filePath);
        
        $pdo->beginTransaction();
        try {
            $ceremony = ensureCeremony($pdo, $ceremonyName);
            $ceremonyId = $ceremony['id'];
            $ceremonySlug = $ceremony['slug'];
            
            $catId = ensureCategory($pdo, $ceremonyId, $categoryName);
            
            $inserted = 0;
            foreach ($rows as $row) {
                $year = isset($row['year']) ? (int)$row['year'] : 0;
                if ($year < 1900 || $year > 2030) continue;
                
                $filmTitle = isset($row['film']) ? trim($row['film']) : '';
                $personName = isset($row['person']) ? trim($row['person']) : '';
                
                if ($filmTitle === 'nan' || empty($filmTitle)) {
                    $filmTitle = $personName;
                }
                if ($personName === 'nan' || empty($personName)) {
                    $personName = $filmTitle;
                }
                if (empty($filmTitle)) continue;
                
                $isWinner = 0;
                if (isset($row['iswinner']) && in_array(strtolower($row['iswinner']), ['true', '1', 'winner', 'yes'])) {
                    $isWinner = 1;
                }
                
                $sourceUrl = $row['sourceurl'] ?? '';
                
                $editionId = ensureEdition($pdo, $ceremonyId, $year, $ceremonySlug);
                $filmId = ensureFilm($pdo, $filmTitle, $year - 1);
                
                insertNomination($pdo, $editionId, $catId, $filmId, 0, $personName, $isWinner, $sourceUrl ?: null);
                $inserted++;
            }
            $pdo->commit();
            echo "Imported $inserted rows.\n";
        } catch (Exception $e) {
            $pdo->rollBack();
            echo "ERROR: " . $e->getMessage() . "\n";
        }
    }
} else {
    echo "Raw directory not found.\n";
}

// ==========================================
// ROUTINE 2: Oscars (scripts/data/the_oscar_award.csv)
// ==========================================
echo "\n=== ROUTINE 2: Importing Academy Awards (Oscars) ===\n";
$oscarFile = __DIR__ . '/data/the_oscar_award.csv';
if (file_exists($oscarFile)) {
    echo "Processing " . basename($oscarFile) . "... \n";
    $rows = parseCsv($oscarFile);
    if (!empty($rows)) {
        $pdo->beginTransaction();
        try {
            $ceremony = ensureCeremony($pdo, "Academy Awards", "United States");
            $ceremonyId = $ceremony['id'];
            $ceremonySlug = $ceremony['slug'];
            
            $inserted = 0;
            $totalRows = count($rows);
            echo "Ingesting $totalRows Oscar entries...\n";
            
            foreach ($rows as $index => $row) {
                $year = isset($row['yearceremony']) ? (int)$row['yearceremony'] : 0;
                $yearFilm = isset($row['yearfilm']) ? (int)$row['yearfilm'] : $year - 1;
                if ($year < 1900 || $year > 2030) continue;
                
                $categoryName = isset($row['category']) ? trim($row['category']) : 'General';
                $filmTitle = isset($row['film']) ? trim($row['film']) : '';
                $nomineeText = isset($row['name']) ? trim($row['name']) : '';
                
                if (empty($filmTitle)) {
                    $filmTitle = $nomineeText;
                }
                if (empty($nomineeText)) {
                    $nomineeText = $filmTitle;
                }
                if (empty($filmTitle)) continue;
                
                $isWinner = 0;
                if (isset($row['winner']) && in_array(strtolower($row['winner']), ['true', '1', 'winner', 'yes'])) {
                    $isWinner = 1;
                }
                
                $editionId = ensureEdition($pdo, $ceremonyId, $year, $ceremonySlug);
                $catId = ensureCategory($pdo, $ceremonyId, $categoryName);
                $filmId = ensureFilm($pdo, $filmTitle, $yearFilm);
                
                insertNomination($pdo, $editionId, $catId, $filmId, 0, $nomineeText, $isWinner, "the_oscar_award.csv");
                $inserted++;
                
                if ($inserted % 5000 === 0) {
                    echo " -> Imported $inserted / $totalRows entries...\n";
                }
            }
            $pdo->commit();
            echo "Successfully imported $inserted Oscar nominations.\n";
        } catch (Exception $e) {
            $pdo->rollBack();
            echo "ERROR: " . $e->getMessage() . "\n";
        }
    } else {
        echo "Empty or error reading Oscars CSV.\n";
    }
} else {
    echo "Oscars file not found.\n";
}

// ==========================================
// ROUTINE 3: South Asian Master CSVs
// ==========================================
echo "\n=== ROUTINE 3: Importing South Asian Master CSVs ===\n";
$southAsianFiles = [
    ['path' => __DIR__ . '/tollywood_scraper/output/tollywood_awards_master.csv', 'country' => 'India'],
    ['path' => __DIR__ . '/mollywood_scraper/output/mollywood_awards_master.csv', 'country' => 'India'],
    ['path' => __DIR__ . '/sandalwood_scraper/output/sandalwood_awards_master.csv', 'country' => 'India']
];

foreach ($southAsianFiles as $sa) {
    $filePath = $sa['path'];
    $country = $sa['country'];
    
    if (file_exists($filePath)) {
        echo "Processing " . basename($filePath) . "... ";
        $rows = parseCsv($filePath);
        if (empty($rows)) {
            echo "Empty or error.\n";
            continue;
        }
        
        $pdo->beginTransaction();
        try {
            $inserted = 0;
            foreach ($rows as $row) {
                if (empty($row['awardshow']) || empty($row['year'])) continue;
                
                $awardShow = trim($row['awardshow']);
                $year = (int)substr(trim($row['year']), 0, 4);
                if ($year < 1900 || $year > 2030) continue;
                
                $categoryName = trim($row['category'] ?? 'General');
                if (strpos($categoryName, 'Unspecified') === 0) {
                    $categoryName = "Best Film/Actor/General";
                }
                
                $filmTitle = isset($row['worktitle']) ? trim($row['worktitle']) : '';
                $nomineeText = isset($row['nomineename']) ? trim($row['nomineename']) : '';
                
                if (empty($filmTitle) || $filmTitle === 'nan') {
                    $filmTitle = $nomineeText;
                }
                if (empty($nomineeText) || $nomineeText === 'nan') {
                    $nomineeText = $filmTitle;
                }
                if (empty($filmTitle) || $filmTitle === 'nan') continue;
                
                $isWinner = 0;
                if (isset($row['result']) && strtolower(trim($row['result'])) === 'winner') {
                    $isWinner = 1;
                }
                
                $language = trim($row['language'] ?? 'Unknown');
                $sourceUrl = trim($row['sourceurl'] ?? '');
                
                $ceremony = ensureCeremony($pdo, $awardShow, $country);
                $ceremonyId = $ceremony['id'];
                $ceremonySlug = $ceremony['slug'];
                
                $editionId = ensureEdition($pdo, $ceremonyId, $year, $ceremonySlug);
                $catId = ensureCategory($pdo, $ceremonyId, $categoryName);
                $filmId = ensureFilm($pdo, $filmTitle, $year - 1, $country, $language);
                
                insertNomination($pdo, $editionId, $catId, $filmId, 0, $nomineeText, $isWinner, $sourceUrl ?: null);
                $inserted++;
            }
            $pdo->commit();
            echo "Imported $inserted rows.\n";
        } catch (Exception $e) {
            $pdo->rollBack();
            echo "ERROR: " . $e->getMessage() . "\n";
        }
    } else {
        echo "Skipping (not found): " . basename($filePath) . "\n";
    }
}

// ==========================================
// UNIVERSAL CSV INGESTION ENGINE
// ==========================================
function ingestUniversalCsv($pdo, string $filePath, string $defaultCeremonyName, string $country, ?string $customSlug = null, ?string $defaultLang = 'English') {
    if (!file_exists($filePath)) {
        echo "Skipping (not found): " . basename($filePath) . "\n";
        return;
    }
    echo "Processing " . basename($filePath) . "... ";
    $rows = parseCsv($filePath);
    if (empty($rows)) {
        echo "Empty or error.\n";
        return;
    }
    
    $ceremony = ensureCeremony($pdo, $defaultCeremonyName, $country, $customSlug);
    $ceremonyId = $ceremony['id'];
    $ceremonySlug = $ceremony['slug'];
    
    $pdo->beginTransaction();
    try {
        $inserted = 0;
        foreach ($rows as $row) {
            $year = null;
            if (isset($row['year'])) $year = (int)substr(trim($row['year']), 0, 4);
            elseif (isset($row['editionyear'])) $year = (int)substr(trim($row['editionyear']), 0, 4);
            
            if (!$year || $year < 1900 || $year > 2030) continue;
            
            $categoryName = 'General';
            if (isset($row['category'])) $categoryName = trim($row['category']);
            elseif (isset($row['categoryname'])) $categoryName = trim($row['categoryname']);
            
            $filmTitle = '';
            if (isset($row['film'])) $filmTitle = trim($row['film']);
            elseif (isset($row['filmtitle'])) $filmTitle = trim($row['filmtitle']);
            
            $nomineeText = '';
            if (isset($row['nominee'])) $nomineeText = trim($row['nominee']);
            elseif (isset($row['nomineetext'])) $nomineeText = trim($row['nomineetext']);
            elseif (isset($row['nomineewinner'])) $nomineeText = trim($row['nomineewinner']);
            elseif (isset($row['winner'])) $nomineeText = trim($row['winner']);
            
            if (empty($filmTitle) || $filmTitle === 'nan') {
                $filmTitle = $nomineeText;
            }
            if (empty($nomineeText) || $nomineeText === 'nan') {
                $nomineeText = $filmTitle;
            }
            if (empty($filmTitle) || $filmTitle === 'nan') continue;
            
            $isWinner = 0;
            if (isset($row['winner']) && (trim($row['winner']) === '1' || strtolower(trim($row['winner'])) === 'winner' || strtolower(trim($row['winner'])) === 'yes')) {
                $isWinner = 1;
            } elseif (isset($row['winnernomineestatus']) && strtolower(trim($row['winnernomineestatus'])) === 'winner') {
                $isWinner = 1;
            } elseif (isset($row['result']) && strtolower(trim($row['result'])) === 'winner') {
                $isWinner = 1;
            }
            
            $sourceUrl = null;
            if (isset($row['sourceurl'])) $sourceUrl = trim($row['sourceurl']);
            elseif (isset($row['source_url'])) $sourceUrl = trim($row['source_url']);
            elseif (isset($row['notes'])) $sourceUrl = trim($row['notes']);
            
            $rowCountry = $country;
            if (isset($row['country']) && !empty(trim($row['country']))) {
                $rowCountry = trim($row['country']);
            }
            
            $rowLang = $defaultLang;
            if (isset($row['lang']) && !empty(trim($row['lang']))) {
                $rowLang = trim($row['lang']);
            } elseif (isset($row['language']) && !empty(trim($row['language']))) {
                $rowLang = trim($row['language']);
            }
            
            $editionId = ensureEdition($pdo, $ceremonyId, $year, $ceremonySlug);
            $catId = ensureCategory($pdo, $ceremonyId, $categoryName);
            $filmId = ensureFilm($pdo, $filmTitle, $year - 1, $rowCountry, $rowLang);
            
            insertNomination($pdo, $editionId, $catId, $filmId, 0, $nomineeText, $isWinner, $sourceUrl ?: null);
            $inserted++;
        }
        $pdo->commit();
        echo "Imported $inserted rows.\n";
    } catch (Exception $e) {
        $pdo->rollBack();
        echo "ERROR: " . $e->getMessage() . "\n";
    }
}

// ==========================================
// ROUTINE 4: Universal Bulk Ingestion
// ==========================================
echo "\n=== ROUTINE 4: Importing Universal Datasets ===\n";

$universalIngests = [
    // Lollywood
    ['path' => __DIR__ . '/../lib/data/lollywood/lux-style-awards.csv', 'name' => 'Lux Style Awards', 'country' => 'Pakistan', 'slug' => 'lux-style-awards', 'lang' => 'Urdu'],
    ['path' => __DIR__ . '/../lib/data/lollywood/nigar-awards.csv', 'name' => 'Nigar Awards', 'country' => 'Pakistan', 'slug' => 'nigar-awards', 'lang' => 'Urdu'],
    ['path' => __DIR__ . '/../lib/data/lollywood/ippa-awards.csv', 'name' => 'IPPA Awards', 'country' => 'Pakistan', 'slug' => 'ippa-awards', 'lang' => 'Urdu'],
    ['path' => __DIR__ . '/../lib/data/lollywood/pisa-awards.csv', 'name' => 'Pakistan International Screen Awards', 'country' => 'Pakistan', 'slug' => 'pisa', 'lang' => 'Urdu'],
    
    // Hollywood & Guilds
    ['path' => __DIR__ . '/../hollywood/saturn_awards/saturn_awards.csv', 'name' => 'Saturn Awards', 'country' => 'United States', 'slug' => 'saturn-awards', 'lang' => 'English'],
    ['path' => __DIR__ . '/../hollywood/annie_awards/annie_awards.csv', 'name' => 'Annie Awards', 'country' => 'United States', 'slug' => 'annie-awards', 'lang' => 'English'],
    ['path' => __DIR__ . '/../hollywood/british_cinema_awards/bafta_film_awards/bafta_awards.csv', 'name' => 'BAFTA Film Awards', 'country' => 'United Kingdom', 'slug' => 'bafta-film-awards', 'lang' => 'English'],
    ['path' => __DIR__ . '/../hollywood/screen_actors_guild_awards/screen_actors_guild_awards.csv', 'name' => 'Screen Actors Guild Awards', 'country' => 'United States', 'slug' => 'sag-awards', 'lang' => 'English'],
    ['path' => __DIR__ . '/../hollywood/dga_awards/dga_awards.csv', 'name' => 'Directors Guild of America Awards', 'country' => 'United States', 'slug' => 'dga-awards', 'lang' => 'English'],
    ['path' => __DIR__ . '/../hollywood/wga_awards/wga_awards.csv', 'name' => 'Writers Guild of America Awards', 'country' => 'United States', 'slug' => 'wga-awards', 'lang' => 'English'],
    ['path' => __DIR__ . '/../hollywood/pga_awards/pga_awards.csv', 'name' => 'Producers Guild of America Awards', 'country' => 'United States', 'slug' => 'pga-awards', 'lang' => 'English'],
    ['path' => __DIR__ . '/../hollywood/critics_choice_awards/critics_choice_awards.csv', 'name' => 'Critics Choice Awards', 'country' => 'United States', 'slug' => 'critics-choice-awards', 'lang' => 'English'],
    ['path' => __DIR__ . '/../hollywood/german_cinema_awards/bavarian_film_awards/bavarian_awards.csv', 'name' => 'Bavarian Film Awards', 'country' => 'Germany', 'slug' => 'bavarian-film-awards', 'lang' => 'German'],
    ['path' => __DIR__ . '/../hollywood/german_cinema_awards/berlin_iff/berlin_awards.csv', 'name' => 'Berlin IFF Golden Bear', 'country' => 'Germany', 'slug' => 'berlin-iff', 'lang' => 'German'],
    ['path' => __DIR__ . '/../hollywood/german_cinema_awards/german_film_awards/lola_awards.csv', 'name' => 'German Film Awards', 'country' => 'Germany', 'slug' => 'german-film-awards', 'lang' => 'German'],
    ['path' => __DIR__ . '/../hollywood/italian_cinema_awards/david_di_donatello_awards/david_awards.csv', 'name' => 'David di Donatello', 'country' => 'Italy', 'slug' => 'david-di-donatello', 'lang' => 'Italian'],
    ['path' => __DIR__ . '/../hollywood/italian_cinema_awards/nastri_dargento_awards/nastri_awards.csv', 'name' => 'Nastri d\'Argento Awards', 'country' => 'Italy', 'slug' => 'nastri-dargento', 'lang' => 'Italian'],
    ['path' => __DIR__ . '/../hollywood/italian_cinema_awards/venice_film_festival/venice_awards.csv', 'name' => 'Venice Film Festival Golden Lion', 'country' => 'Italy', 'slug' => 'venice-film-festival', 'lang' => 'Italian'],
    ['path' => __DIR__ . '/../hollywood/spirit_awards/spirit_awards.csv', 'name' => 'Independent Spirit Awards', 'country' => 'United States', 'slug' => 'independent-spirit-awards', 'lang' => 'English'],
    ['path' => __DIR__ . '/../hollywood/british_cinema_awards/evening_standard_british_film_awards/evening_standard_awards.csv', 'name' => 'Evening Standard British Film Awards', 'country' => 'United Kingdom', 'slug' => 'evening-standard-awards', 'lang' => 'English'],
    ['path' => __DIR__ . '/../hollywood/british_cinema_awards/london_film_critics_circle_awards/london_critics_awards.csv', 'name' => 'London Film Critics Circle Awards', 'country' => 'United Kingdom', 'slug' => 'lfcc-awards', 'lang' => 'English'],
    
    // Pan-African
    ['path' => __DIR__ . '/../african_cinema/pan_african_cinema_awards/fespaco_etalon_dor/fespaco_awards.csv', 'name' => 'FESPACO Etalon d\'Or', 'country' => 'Burkina Faso', 'slug' => 'fespaco', 'lang' => 'French'],
    ['path' => __DIR__ . '/../african_cinema/pan_african_cinema_awards/carthage_film_festival_awards/carthage_awards.csv', 'name' => 'Carthage Film Festival Awards', 'country' => 'Tunisia', 'slug' => 'carthage-film-festival', 'lang' => 'Arabic'],
    ['path' => __DIR__ . '/../african_cinema/pan_african_cinema_awards/zanzibar_iff_awards/zanzibar_iff_awards.csv', 'name' => 'Zanzibar IFF Awards', 'country' => 'Tanzania', 'slug' => 'ziff-awards', 'lang' => 'English'],
    ['path' => __DIR__ . '/../african_cinema/pan_african_cinema_awards/african_cinematography_awards/african_cinematography_awards.csv', 'name' => 'African Cinematography Awards', 'country' => 'Global', 'slug' => 'african-cinematography-awards', 'lang' => 'English'],
    ['path' => __DIR__ . '/../african_cinema/pan_african_cinema_awards/el_gouna_film_festival_awards/el_gouna_awards.csv', 'name' => 'El Gouna Film Festival Awards', 'country' => 'Egypt', 'slug' => 'el-gouna-film-festival', 'lang' => 'Arabic'],
    
    // MENA & Regional
    ['path' => __DIR__ . '/iran_cinema_celebration.csv', 'name' => 'Iran Cinema Celebration Awards', 'country' => 'Iran', 'slug' => 'iran-cinema-celebration', 'lang' => 'Persian'],
    ['path' => __DIR__ . '/golden_tulip_awards.csv', 'name' => 'Golden Tulip Awards', 'country' => 'Turkey', 'slug' => 'golden-tulip-awards', 'lang' => 'Turkish'],
    ['path' => __DIR__ . '/arab_cinema_awards.csv', 'name' => 'Arab Cinema Awards', 'country' => 'Global', 'slug' => 'arab-cinema-awards', 'lang' => 'Arabic'],
    ['path' => __DIR__ . '/marrakech_awards.csv', 'name' => 'Marrakech IFF Awards', 'country' => 'Morocco', 'slug' => 'marrakech-iff', 'lang' => 'French'],
    ['path' => __DIR__ . '/dubai_iff_awards.csv', 'name' => 'Dubai International Film Festival Awards', 'country' => 'United Arab Emirates', 'slug' => 'diff', 'lang' => 'Arabic'],
    
    // Others
    ['path' => __DIR__ . '/tollywood_scraper/output/sun_kudumbam_virudhugal.csv', 'name' => 'Sun Kudumbam Virudhugal', 'country' => 'India', 'slug' => 'sun-kudumbam-virudhugal', 'lang' => 'Tamil'],
    ['path' => __DIR__ . '/sandalwood_scraper/output/suvarna_film_awards.csv', 'name' => 'Suvarna Film Awards', 'country' => 'India', 'slug' => 'suvarna-film-awards', 'lang' => 'Kannada'],
];

foreach ($universalIngests as $item) {
    ingestUniversalCsv($pdo, $item['path'], $item['name'], $item['country'], $item['slug'], $item['lang']);
}

echo "\nDone ingesting all remaining CSVs!\n";
