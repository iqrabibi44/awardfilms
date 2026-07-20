<?php
require_once __DIR__ . '/config/DB.php';

$filmId = $_GET['film'] ?? null;
$personId = $_GET['person'] ?? null;
$imageUrl = $_GET['url'] ?? null;
$ceremonySlug = $_GET['ceremony'] ?? null;

$cacheExpiryDays = 30;

function servePlaceholderSVG($isPerson, $iconOverride = null) {
    header('Content-Type: image/svg+xml');
    header('Cache-Control: public, max-age=86400'); // 1 day
    $icon = $iconOverride ?: ($isPerson ? '👤' : '🎬');
    $svg = <<<SVG
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 750" width="100%" height="100%">
    <rect width="100%" height="100%" fill="#0a192f" />
    <rect width="100%" height="100%" fill="none" stroke="#d4af37" stroke-width="4" stroke-opacity="0.2" />
    <text x="50%" y="50%" font-family="sans-serif" font-size="100" fill="#d4af37" text-anchor="middle" dominant-baseline="central">$icon</text>
</svg>
SVG;
    echo $svg;
    exit;
}

// ─── CASE A: DYNAMIC WEB IMAGE URL REVERSE PROXY ───
if ($imageUrl) {
    $imageUrl = filter_var($imageUrl, FILTER_SANITIZE_URL);
    if (!filter_var($imageUrl, FILTER_VALIDATE_URL)) {
        http_response_code(400);
        exit("Invalid source URL");
    }

    $cacheDir = __DIR__ . '/cache/url_images';
    if (!is_dir($cacheDir)) {
        mkdir($cacheDir, 0777, true);
    }
    
    $cacheFile = $cacheDir . '/' . md5($imageUrl) . '.jpg';
    
    if (file_exists($cacheFile)) {
        $fileAge = time() - filemtime($cacheFile);
        if ($fileAge < ($cacheExpiryDays * 24 * 60 * 60)) {
            header('Content-Type: image/jpeg');
            header('Cache-Control: public, max-age=' . ($cacheExpiryDays * 24 * 60 * 60));
            readfile($cacheFile);
            exit;
        }
    }
    
    $ctx = stream_context_create([
        'http' => [
            'timeout' => 8,
            'header' => "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\nReferer: https://en.wikipedia.org/\r\n"
        ]
    ]);
    
    $imageData = @file_get_contents($imageUrl, false, $ctx);
    
    if ($imageData) {
        file_put_contents($cacheFile, $imageData);
        header('Content-Type: image/jpeg');
        header('Cache-Control: public, max-age=' . ($cacheExpiryDays * 24 * 60 * 60));
        echo $imageData;
        exit;
    } else {
        servePlaceholderSVG(false);
    }
}

// ─── CASE B: CEREMONY DYNAMIC WIKIPEDIA LOGO PROXY ───
if ($ceremonySlug) {
    // 1. Check if there is a local asset in /images/ceremonies/ first
    $localPng = __DIR__ . '/images/ceremonies/' . $ceremonySlug . '.png';
    $localJpg = __DIR__ . '/images/ceremonies/' . $ceremonySlug . '.jpg';
    
    if (file_exists($localPng)) {
        header('Content-Type: image/png');
        header('Cache-Control: public, max-age=' . ($cacheExpiryDays * 24 * 60 * 60));
        readfile($localPng);
        exit;
    }
    if (file_exists($localJpg)) {
        header('Content-Type: image/jpeg');
        header('Cache-Control: public, max-age=' . ($cacheExpiryDays * 24 * 60 * 60));
        readfile($localJpg);
        exit;
    }

    $cacheDir = __DIR__ . '/cache/ceremonies';
    if (!is_dir($cacheDir)) {
        mkdir($cacheDir, 0777, true);
    }
    $cacheFile = $cacheDir . '/' . $ceremonySlug . '.jpg';
    
    if (file_exists($cacheFile)) {
        $fileAge = time() - filemtime($cacheFile);
        if ($fileAge < ($cacheExpiryDays * 24 * 60 * 60)) {
            header('Content-Type: image/jpeg');
            header('Cache-Control: public, max-age=' . ($cacheExpiryDays * 24 * 60 * 60));
            readfile($cacheFile);
            exit;
        }
    }
    
    // Lookup ceremony name in DB
    $pdo = DB::connection();
    $stmt = $pdo->prepare("SELECT name FROM ceremonies WHERE slug = ? LIMIT 1");
    $stmt->execute([$ceremonySlug]);
    $ceremonyName = $stmt->fetchColumn();
    
    $resolvedUrl = null;
    if ($ceremonyName) {
        $searchTerm = str_ireplace(' Norway', '', $ceremonyName);
        
        $wikiUrl = "https://en.wikipedia.org/w/api.php?action=query&titles=" . urlencode($searchTerm) . "&prop=pageimages&format=json&pithumbsize=600&redirects=true";
        $ctx = stream_context_create([
            'http' => [
                'timeout' => 5,
                'header' => "User-Agent: AwardFilms/1.0 (contact@awardfilms.com)\r\n"
            ]
        ]);
        $response = @file_get_contents($wikiUrl, false, $ctx);
        if ($response) {
            $data = json_decode($response, true);
            if (!empty($data['query']['pages'])) {
                $page = reset($data['query']['pages']);
                if (!empty($page['thumbnail']['source'])) {
                    $resolvedUrl = $page['thumbnail']['source'];
                }
            }
        }
    }
    
    if ($resolvedUrl) {
        $imageData = @file_get_contents($resolvedUrl, false, $ctx);
        if ($imageData) {
            file_put_contents($cacheFile, $imageData);
            header('Content-Type: image/jpeg');
            header('Cache-Control: public, max-age=' . ($cacheExpiryDays * 24 * 60 * 60));
            echo $imageData;
            exit;
        }
    }
    
    // Curated high quality fallbacks if Wikipedia returns nothing
    $fallbacks = [
        'lux-style-awards' => 'https://images.unsplash.com/photo-1518173946687-a4c8a383392e?q=80&w=600',
        'nigar-awards' => 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=600',
        'ippa-awards' => 'https://images.unsplash.com/photo-1507676184212-d03ab07a01bf?q=80&w=600',
        'pisa-awards' => 'https://images.unsplash.com/photo-1514306191717-452ec28c7814?q=80&w=600',
        'default' => 'https://images.unsplash.com/photo-1514306191717-452ec28c7814?q=80&w=600'
    ];
    $fallbackUrl = $fallbacks[$ceremonySlug] ?? $fallbacks['default'];
    
    $imageData = @file_get_contents($fallbackUrl, false, stream_context_create(['http' => ['timeout' => 5]]));
    if ($imageData) {
        file_put_contents($cacheFile, $imageData);
        header('Content-Type: image/jpeg');
        header('Cache-Control: public, max-age=' . ($cacheExpiryDays * 24 * 60 * 60));
        echo $imageData;
        exit;
    }
    
    servePlaceholderSVG(false, '🏆');
}

// ─── CASE C: FILM OR PERSON ID PROXY ───
$isPerson = $personId !== null;
$id = $isPerson ? $personId : $filmId;

if (!$id) {
    http_response_code(400);
    exit("Invalid request parameters");
}

if (!is_numeric($id)) {
    http_response_code(400);
    exit("Invalid ID format");
}

$cacheDir = __DIR__ . '/cache/posters';
if (!is_dir($cacheDir)) {
    mkdir($cacheDir, 0777, true);
}
$cacheFile = $cacheDir . '/' . ($isPerson ? 'person_' : '') . $id . '.jpg';

if (file_exists($cacheFile)) {
    $fileAge = time() - filemtime($cacheFile);
    if ($fileAge < ($cacheExpiryDays * 24 * 60 * 60)) {
        header('Content-Type: image/jpeg');
        header('Cache-Control: public, max-age=' . ($cacheExpiryDays * 24 * 60 * 60));
        readfile($cacheFile);
        exit;
    }
}

$pdo = DB::connection();
$posterUrl = null;
$apiKey = '5b840d0df49fca6fefa830d98e674c8c';

if ($isPerson) {
    $stmt = $pdo->prepare("SELECT id, name, image_url FROM persons WHERE id = :id");
    $stmt->execute(['id' => $id]);
    $person = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$person) {
        servePlaceholderSVG(true);
    }
    
    $posterUrl = $person['image_url'];
    
    if (empty($posterUrl) && $posterUrl !== 'N/A') {
        $searchUrl = "https://api.themoviedb.org/3/search/person?api_key={$apiKey}&query=" . urlencode($person['name']);
        $ctx = stream_context_create(['http' => ['timeout' => 5]]);
        $response = @file_get_contents($searchUrl, false, $ctx);
        if ($response) {
            $data = json_decode($response, true);
            if (!empty($data['results'][0]['profile_path'])) {
                $posterUrl = 'https://image.tmdb.org/t/p/w500' . $data['results'][0]['profile_path'];
            }
        }
        $updateUrl = $posterUrl ?: 'N/A';
        $updateStmt = $pdo->prepare("UPDATE persons SET image_url = :url WHERE id = :id");
        $updateStmt->execute(['url' => $updateUrl, 'id' => $id]);
    }
    if ($posterUrl === 'N/A') $posterUrl = null;
} else {
    $stmt = $pdo->prepare("SELECT id, title, year, poster_url, tmdb_id FROM films WHERE id = :id");
    $stmt->execute(['id' => $id]);
    $film = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$film) {
        servePlaceholderSVG(false);
    }
    
    $posterUrl = $film['poster_url'];
    
    if (empty($posterUrl) && $film['tmdb_id'] != -1) {
        $searchUrl = "https://api.themoviedb.org/3/search/movie?api_key={$apiKey}&query=" . urlencode($film['title']);
        if (!empty($film['year'])) {
            $searchUrl .= "&primary_release_year=" . urlencode($film['year']);
        }
        $ctx = stream_context_create(['http' => ['timeout' => 5]]);
        $response = @file_get_contents($searchUrl, false, $ctx);
        
        $tmdbId = -1;
        if ($response) {
            $data = json_decode($response, true);
            if (!empty($data['results'][0]['poster_path'])) {
                $posterUrl = 'https://image.tmdb.org/t/p/w500' . $data['results'][0]['poster_path'];
                $tmdbId = $data['results'][0]['id'];
            } else if (!empty($film['year'])) {
                $fallbackUrl = "https://api.themoviedb.org/3/search/movie?api_key={$apiKey}&query=" . urlencode($film['title']);
                $fallbackResp = @file_get_contents($fallbackUrl, false, $ctx);
                if ($fallbackResp) {
                    $fallbackData = json_decode($fallbackResp, true);
                    if (!empty($fallbackData['results'][0]['poster_path'])) {
                        $posterUrl = 'https://image.tmdb.org/t/p/w500' . $fallbackData['results'][0]['poster_path'];
                        $tmdbId = $fallbackData['results'][0]['id'];
                    }
                }
            }
        }
        
        $updateStmt = $pdo->prepare("UPDATE films SET poster_url = :url, tmdb_id = :tmdb_id WHERE id = :id");
        $updateStmt->execute([
            'url' => $posterUrl,
            'tmdb_id' => $tmdbId,
            'id' => $id
        ]);
    }
}

if (empty($posterUrl)) {
    servePlaceholderSVG($isPerson);
}

$ctx = stream_context_create(['http' => ['timeout' => 8]]);
$imageData = @file_get_contents($posterUrl, false, $ctx);

if ($imageData) {
    file_put_contents($cacheFile, $imageData);
    header('Content-Type: image/jpeg');
    header('Cache-Control: public, max-age=' . ($cacheExpiryDays * 24 * 60 * 60));
    echo $imageData;
} else {
    servePlaceholderSVG($isPerson);
}
?>
