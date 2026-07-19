<?php
require_once __DIR__ . '/../config/DB.php';
require_once __DIR__ . '/../lib/queries.php';

function profileQuery($label, $callable) {
    $t = microtime(true);
    $callable();
    $d = microtime(true) - $t;
    echo "$label took: {$d}s\n";
}

profileQuery("1. getFilmsByDecade(2020, 2029)", function() {
    getFilmsByDecade(2020, 2029, 24, 0);
});

profileQuery("2. getFilmsByDecade(1990, 1999)", function() {
    getFilmsByDecade(1990, 1999, 24, 0);
});

profileQuery("3. getFilmsByGenre('Action')", function() {
    getFilmsByGenre("Action", 24, 0);
});

profileQuery("4. getFilmsByGenre('Drama')", function() {
    getFilmsByGenre("Drama", 24, 0);
});

profileQuery("5. getFilmsByCountry('India')", function() {
    getFilmsByCountry("India", 24, 0);
});

profileQuery("6. getFilmsByCountry('United States')", function() {
    getFilmsByCountry("United States", 24, 0);
});
