<?php
// router.php for PHP built-in server
if (preg_match('/\.(?:png|jpg|jpeg|gif|css|js|ico|ttf|woff|woff2)$/', $_SERVER["REQUEST_URI"])) {
    return false;    // serve the requested resource as-is.
}

$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$uri = ltrim($uri, '/');
error_log("Router matching URI: " . $_SERVER['REQUEST_URI'] . " | parsed: " . $uri);

// Emulate .htaccess routing rules
if ($uri === 'privacy') { include 'privacy.php'; return; }
if ($uri === 'search') { include 'search-results.php'; return; }
if ($uri === 'browse') { include 'browse.php'; return; }
if ($uri === 'films') { include 'films.php'; return; }
if ($uri === 'persons') { include 'persons.php'; return; }

if (preg_match('~^browse/country/([^/]+)$~', $uri, $m)) {
    $_GET['country'] = $m[1];
    include 'browse-country-details.php';
    return;
}
if (preg_match('~^browse/country$~', $uri)) {
    include 'browse-country.php';
    return;
}
if (preg_match('~^browse/decade/([^/]+)$~', $uri, $m)) {
    $_GET['decade'] = $m[1];
    include 'browse-decade.php';
    return;
}
if (preg_match('~^browse/genre/([^/]+)$~', $uri, $m)) {
    $_GET['genre'] = $m[1];
    include 'browse-genre.php';
    return;
}
if (preg_match('~^cinema/([^/]+)$~', $uri, $m)) {
    $_GET['supercategory'] = $m[1];
    include 'cinema.php';
    return;
}
if (preg_match('~^cinema/([^/]+)/([^/]+)$~', $uri, $m)) {
    $_GET['supercategory'] = $m[1];
    $_GET['industry'] = $m[2];
    include 'industry.php';
    return;
}
if (preg_match('~^films/([^/]+)$~', $uri, $m)) {
    $_GET['slug'] = $m[1];
    include 'film-details.php';
    return;
}
if (preg_match('~^persons/([^/]+)$~', $uri, $m)) {
    $_GET['slug'] = $m[1];
    include 'person-details.php';
    return;
}
if (preg_match('~^([^/]+)/([^/]+)/([^/]+)$~', $uri, $m) && !preg_match('~^(assets|config|lib|layouts)~', $uri)) {
    $_GET['supercategory'] = $m[1];
    $_GET['industry'] = $m[2];
    $_GET['ceremony'] = $m[3];
    include 'ceremony.php';
    return;
}
if (preg_match('~^([^/]+)/([^/]+)/([^/]+)/([^/]+)$~', $uri, $m) && !preg_match('~^(assets|config|lib|layouts)~', $uri)) {
    $_GET['supercategory'] = $m[1];
    $_GET['industry'] = $m[2];
    $_GET['ceremony'] = $m[3];
    $_GET['slug'] = $m[4];
    include 'edition.php';
    return;
}

if ($uri === '') {
    include 'index.php';
    return;
}

if (file_exists(__DIR__ . '/' . $uri)) {
    return false;
}

http_response_code(404);
echo "Not Found: " . htmlspecialchars($uri);
