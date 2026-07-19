<?php
/**
 * Safe Local CSV Importer Utility
 * Parses award nomination CSV files and upserts records to the database.
 */
require_once __DIR__ . '/../config/DB.php';

class CSVImporter
{
    /**
     * Parses the CSV file and imports it using custom upsert rules.
     */
    public static function import(string $filePath): array
    {
        $pdo = DB::connection();
        
        $stats = [
            'total_rows'           => 0,
            'skipped_rows'         => 0,
            'ceremonies_created'   => 0,
            'editions_created'     => 0,
            'categories_created'   => 0,
            'films_created'        => 0,
            'persons_created'      => 0,
            'nominations_inserted' => 0,
            'nominations_updated'  => 0,
            'errors'               => []
        ];

        if (($handle = fopen($filePath, "r")) === false) {
            throw new Exception("Could not open CSV file.");
        }

        // Parse header row
        $headers = fgetcsv($handle, 0, ',', '"', '\\');
        if (!$headers) {
            fclose($handle);
            throw new Exception("CSV file has no headers or is empty.");
        }

        // Clean headers for mapping
        $cleanHeaders = array_map(function($h) {
            return strtolower(trim(str_replace([' ', '_', '-'], '', $h)));
        }, $headers);

        $headerMap = [
            'year'       => array_search('year', $cleanHeaders),
            'ceremony'   => array_search('ceremony', $cleanHeaders) !== false ? array_search('ceremony', $cleanHeaders) : array_search('awardname', $cleanHeaders),
            'category'   => array_search('category', $cleanHeaders),
            'nominee'    => array_search('nominee', $cleanHeaders),
            'film'       => array_search('film', $cleanHeaders),
            'country'    => array_search('country', $cleanHeaders),
            'winner'     => array_search('winner', $cleanHeaders) !== false ? array_search('winner', $cleanHeaders) : array_search('won', $cleanHeaders),
            'source_url' => array_search('sourceurl', $cleanHeaders) !== false ? array_search('sourceurl', $cleanHeaders) : array_search('sourceref', $cleanHeaders)
        ];

        // Validate essential headers
        if ($headerMap['year'] === false || $headerMap['ceremony'] === false || $headerMap['category'] === false) {
            fclose($handle);
            throw new Exception("CSV structure error. Must contain: 'year', 'ceremony' (or 'Award Name'), and 'category'.");
        }

        $pdo->beginTransaction();

        try {
            $rowNum = 0;
            while (($row = fgetcsv($handle, 0, ',', '"', '\\')) !== false) {
                $rowNum++;
                $stats['total_rows']++;

                // Read matching values
                $year         = isset($row[$headerMap['year']]) ? (int)$row[$headerMap['year']] : 0;
                $ceremonyName = isset($row[$headerMap['ceremony']]) ? trim($row[$headerMap['ceremony']]) : '';
                $categoryName = isset($row[$headerMap['category']]) ? trim($row[$headerMap['category']]) : '';
                $nomineeText  = isset($row[$headerMap['nominee']]) ? trim($row[$headerMap['nominee']]) : '';
                $filmTitle    = isset($row[$headerMap['film']]) ? trim($row[$headerMap['film']]) : '';
                $country      = isset($row[$headerMap['country']]) ? trim($row[$headerMap['country']]) : '';
                $winnerRaw    = isset($row[$headerMap['winner']]) ? trim($row[$headerMap['winner']]) : '0';
                $sourceUrl    = isset($row[$headerMap['source_url']]) ? trim($row[$headerMap['source_url']]) : '';

                if (empty($year) || empty($ceremonyName) || empty($categoryName)) {
                    $stats['skipped_rows']++;
                    $stats['errors'][] = "Row #{$rowNum} skipped: Missing Year, Ceremony, or Category values.";
                    continue;
                }

                // Determine win status
                $isWinner = in_array(strtolower($winnerRaw), ['1', 'true', 'yes', 'winner']) ? 1 : 0;

                // 1. Ceremony Upsert/Find
                $stmt = $pdo->prepare("SELECT id, slug FROM ceremonies WHERE name = ? LIMIT 1");
                $stmt->execute([$ceremonyName]);
                $ceremony = $stmt->fetch();

                if (!$ceremony) {
                    $cSlug = self::makeSlug($ceremonyName);
                    // Ensure unique slug
                    $check = $pdo->prepare("SELECT id FROM ceremonies WHERE slug = ?");
                    $check->execute([$cSlug]);
                    if ($check->fetch()) {
                        $cSlug .= '-' . uniqid();
                    }
                    $ins = $pdo->prepare("INSERT INTO ceremonies (slug, name, country) VALUES (?, ?, ?)");
                    $ins->execute([$cSlug, $ceremonyName, $country ?: null]);
                    $ceremonyId = $pdo->lastInsertId();
                    $ceremonySlug = $cSlug;
                    $stats['ceremonies_created']++;
                } else {
                    $ceremonyId = $ceremony['id'];
                    $ceremonySlug = $ceremony['slug'];
                }

                // 2. Edition Upsert/Find
                $stmt = $pdo->prepare("SELECT id FROM editions WHERE ceremony_id = ? AND year = ? LIMIT 1");
                $stmt->execute([$ceremonyId, $year]);
                $edition = $stmt->fetch();

                if (!$edition) {
                    $eSlug = $ceremonySlug . '-' . $year;
                    // Ensure unique slug
                    $check = $pdo->prepare("SELECT id FROM editions WHERE slug = ?");
                    $check->execute([$eSlug]);
                    if ($check->fetch()) {
                        $eSlug .= '-' . uniqid();
                    }
                    $ins = $pdo->prepare("INSERT INTO editions (ceremony_id, year, slug) VALUES (?, ?, ?)");
                    $ins->execute([$ceremonyId, $year, $eSlug]);
                    $editionId = $pdo->lastInsertId();
                    $stats['editions_created']++;
                } else {
                    $editionId = $edition['id'];
                }

                // 3. Category Upsert/Find
                $stmt = $pdo->prepare("SELECT id FROM categories WHERE ceremony_id = ? AND name = ? LIMIT 1");
                $stmt->execute([$ceremonyId, $categoryName]);
                $category = $stmt->fetch();

                if (!$category) {
                    $catSlug = self::makeSlug($categoryName);
                    // Ensure unique slug
                    $check = $pdo->prepare("SELECT id FROM categories WHERE ceremony_id = ? AND slug = ?");
                    $check->execute([$ceremonyId, $catSlug]);
                    if ($check->fetch()) {
                        $catSlug .= '-' . uniqid();
                    }
                    $ins = $pdo->prepare("INSERT INTO categories (ceremony_id, name, slug) VALUES (?, ?, ?)");
                    $ins->execute([$ceremonyId, $categoryName, $catSlug]);
                    $categoryId = $pdo->lastInsertId();
                    $stats['categories_created']++;
                } else {
                    $categoryId = $category['id'];
                }

                // 4. Film Upsert/Find
                $filmId = null;
                if (!empty($filmTitle)) {
                    $stmt = $pdo->prepare("SELECT id FROM films WHERE title = ? LIMIT 1");
                    $stmt->execute([$filmTitle]);
                    $film = $stmt->fetch();

                    if (!$film) {
                        $fSlug = self::makeSlug($filmTitle);
                        $check = $pdo->prepare("SELECT id FROM films WHERE slug = ?");
                        $check->execute([$fSlug]);
                        if ($check->fetch()) {
                            $fSlug .= '-' . uniqid();
                        }
                        $ins = $pdo->prepare("INSERT INTO films (slug, title, year, country) VALUES (?, ?, ?, ?)");
                        $ins->execute([$fSlug, $filmTitle, $year, $country ?: null]);
                        $filmId = $pdo->lastInsertId();
                        $stats['films_created']++;
                    } else {
                        $filmId = $film['id'];
                    }
                }

                // 5. Person Upsert/Find
                $personId = null;
                if (!empty($nomineeText) && strtolower($nomineeText) !== strtolower($filmTitle)) {
                    $stmt = $pdo->prepare("SELECT id FROM persons WHERE name = ? LIMIT 1");
                    $stmt->execute([$nomineeText]);
                    $person = $stmt->fetch();

                    if (!$person) {
                        $pSlug = self::makeSlug($nomineeText);
                        $check = $pdo->prepare("SELECT id FROM persons WHERE slug = ?");
                        $check->execute([$pSlug]);
                        if ($check->fetch()) {
                            $pSlug .= '-' . uniqid();
                        }
                        $ins = $pdo->prepare("INSERT INTO persons (slug, name) VALUES (?, ?)");
                        $ins->execute([$pSlug, $nomineeText]);
                        $personId = $pdo->lastInsertId();
                        $stats['persons_created']++;
                    } else {
                        $personId = $person['id'];
                    }
                }

                // 6. Nomination Upsert via ON DUPLICATE KEY UPDATE
                $ins = $pdo->prepare("
                    INSERT INTO nominations (edition_id, category_id, film_id, person_id, nominee_text, is_winner, source_ref) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON DUPLICATE KEY UPDATE 
                        is_winner = VALUES(is_winner),
                        source_ref = COALESCE(VALUES(source_ref), source_ref),
                        person_id = COALESCE(VALUES(person_id), person_id)
                ");
                $ins->execute([$editionId, $categoryId, $filmId, $personId, $nomineeText, $isWinner, $sourceUrl ?: null]);
                
                if ($ins->rowCount() == 1) {
                    $stats['nominations_inserted']++;
                } elseif ($ins->rowCount() == 2) {
                    $stats['nominations_updated']++;
                }
            }

            $pdo->commit();
        } catch (Exception $e) {
            $pdo->rollBack();
            fclose($handle);
            throw $e;
        }

        fclose($handle);
        return $stats;
    }

    /**
     * Converts a string into a clean lowercase URL slug.
     */
    private static function makeSlug(string $text): string
    {
        $text = preg_replace('~[^\pL\d]+~u', '-', $text);
        if (function_exists('iconv')) {
            $text = iconv('utf-8', 'us-ascii//TRANSLIT', $text);
        }
        $text = preg_replace('~[^-\w]+~', '', $text);
        $text = trim($text, '-');
        $text = preg_replace('~-+~', '-', $text);
        $text = strtolower($text);
        return empty($text) ? 'n-a' : $text;
    }
}
