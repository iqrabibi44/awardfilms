<?php
require_once __DIR__ . '/../config/DB.php';

$apiKey = '5b840d0df49fca6fefa830d98e674c8c';
$pdo = DB::connection();

$limit = 20;

// 1. Process Films (Posters, Genres, Countries)
echo "=== Processing Films (Posters, Genres, Countries) ===\n";
$stmt = $pdo->prepare("
    SELECT id, title, year, poster_url, tmdb_id, genre, country 
    FROM films 
    WHERE ((poster_url IS NULL OR poster_url = '') 
       OR (genre IS NULL OR genre = '') 
       OR (country IS NULL OR country = ''))
      AND (tmdb_id IS NULL OR tmdb_id != -1)
    LIMIT :limit
");
$stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
$stmt->execute();
$films = $stmt->fetchAll(PDO::FETCH_ASSOC);

$totalFilms = count($films);
echo "Found $totalFilms films to process.\n";

$ctx = stream_context_create(['http' => ['timeout' => 5]]);
$processedFilms = 0;

foreach ($films as $film) {
    $processedFilms++;
    $title = $film['title'];
    $year = $film['year'];
    $tmdbId = $film['tmdb_id'];
    
    // Step 1: Find TMDb ID if missing
    if (!$tmdbId) {
        $searchUrl = "https://api.themoviedb.org/3/search/movie?api_key={$apiKey}&query=" . urlencode($title);
        if (!empty($year)) $searchUrl .= "&primary_release_year=" . urlencode($year);
        
        $response = @file_get_contents($searchUrl, false, $ctx);
        usleep(300000);
        
        if ($response) {
            $data = json_decode($response, true);
            if (!empty($data['results'][0]['id'])) {
                $tmdbId = $data['results'][0]['id'];
            }
        }
        
        // Fallback without year
        if (!$tmdbId && !empty($year)) {
            $fallbackUrl = "https://api.themoviedb.org/3/search/movie?api_key={$apiKey}&query=" . urlencode($title);
            $response = @file_get_contents($fallbackUrl, false, $ctx);
            usleep(300000);
            if ($response) {
                $data = json_decode($response, true);
                if (!empty($data['results'][0]['id'])) {
                    $tmdbId = $data['results'][0]['id'];
                }
            }
        }
    }
    
    // Step 2: Fetch Details using TMDb ID
    if ($tmdbId && $tmdbId != -1) {
        $detailsUrl = "https://api.themoviedb.org/3/movie/{$tmdbId}?api_key={$apiKey}";
        $response = @file_get_contents($detailsUrl, false, $ctx);
        usleep(300000);
        
        if ($response) {
            $data = json_decode($response, true);
            $posterUrl = !empty($data['poster_path']) ? 'https://image.tmdb.org/t/p/w500' . $data['poster_path'] : 'N/A';
            
            $genres = [];
            if (!empty($data['genres'])) {
                foreach ($data['genres'] as $g) $genres[] = $g['name'];
            }
            $genreStr = implode(', ', $genres) ?: 'N/A';
            
            $countries = [];
            if (!empty($data['production_countries'])) {
                foreach ($data['production_countries'] as $c) $countries[] = $c['name'];
            }
            $countryStr = implode(', ', $countries) ?: 'N/A';
            
            $updateStmt = $pdo->prepare("UPDATE films SET poster_url = :url, tmdb_id = :tmdb_id, genre = :genre, country = :country WHERE id = :id");
            $updateStmt->execute([
                'url' => $posterUrl,
                'tmdb_id' => $tmdbId,
                'genre' => $genreStr,
                'country' => $countryStr,
                'id' => $film['id']
            ]);
            echo "[$processedFilms/$totalFilms] Film '$title': Updated Poster, Genre($genreStr), Country($countryStr)\n";
        }
    } else {
        // Mark as not found
        $updateStmt = $pdo->prepare("UPDATE films SET tmdb_id = -1, poster_url = 'N/A', genre = 'N/A', country = 'N/A' WHERE id = :id");
        $updateStmt->execute(['id' => $film['id']]);
        echo "[$processedFilms/$totalFilms] Film '$title': Not found on TMDb.\n";
    }
}

echo "\n=== Processing Persons (Photos) ===\n";
// 2. Process Persons
$stmt = $pdo->prepare("
    SELECT id, name 
    FROM persons 
    WHERE (image_url IS NULL OR image_url = '') 
    LIMIT :limit
");
$stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
$stmt->execute();
$persons = $stmt->fetchAll(PDO::FETCH_ASSOC);

$totalPersons = count($persons);
echo "Found $totalPersons persons to process.\n";

$processedPersons = 0;
$foundPersons = 0;

foreach ($persons as $person) {
    $processedPersons++;
    $name = $person['name'];
    
    $searchUrl = "https://api.themoviedb.org/3/search/person?api_key={$apiKey}&query=" . urlencode($name);
    $response = @file_get_contents($searchUrl, false, $ctx);
    usleep(300000);
    
    $imageUrl = 'N/A';
    if ($response) {
        $data = json_decode($response, true);
        if (!empty($data['results'][0]['profile_path'])) {
            $imageUrl = 'https://image.tmdb.org/t/p/w500' . $data['results'][0]['profile_path'];
            $foundPersons++;
            echo "[$processedPersons/$totalPersons] Found photo for '$name': $imageUrl\n";
        } else {
            echo "[$processedPersons/$totalPersons] No photo found for '$name'\n";
        }
    } else {
        echo "[$processedPersons/$totalPersons] Failed to query TMDb for '$name'\n";
    }
    
    $updateStmt = $pdo->prepare("UPDATE persons SET image_url = :url WHERE id = :id");
    $updateStmt->execute([
        'url' => $imageUrl,
        'id' => $person['id']
    ]);
}

echo "\nDone! Processed $processedFilms films and $processedPersons persons ($foundPersons photos found).\n";
