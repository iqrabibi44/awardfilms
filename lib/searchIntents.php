<?php
// lib/searchIntents.php

class SearchIntents {
    public static $winnerWords = ["won", "winner", "wins", "jeeta", "took home", "victory", "winners"];
    public static $nomineeWords = ["nominated", "nomination", "nominee", "shortlisted", "nominations", "nominees"];
    public static $filmWords = ["movie", "movies", "film", "films"];
    public static $personWords = ["actor", "actress", "director", "who", "filmmaker", "people", "persons", "person"];
    public static $categoryWords = [
        "best actor" => ["best actor", "actor", "hero"],
        "best actress" => ["best actress", "actress", "heroine"],
        "best film" => ["best film", "best picture", "best movie", "film", "picture"],
        "best director" => ["best director", "director"]
    ];
    public static $decadeMap = [
        "1920s" => [1920, 1929], "20s" => [1920, 1929],
        "1930s" => [1930, 1939], "30s" => [1930, 1939],
        "1940s" => [1940, 1949], "40s" => [1940, 1949],
        "1950s" => [1950, 1959], "50s" => [1950, 1959],
        "1960s" => [1960, 1969], "60s" => [1960, 1969],
        "1970s" => [1970, 1979], "70s" => [1970, 1979],
        "1980s" => [1980, 1989], "80s" => [1980, 1989],
        "1990s" => [1990, 1999], "90s" => [1990, 1999],
        "2000s" => [2000, 2009], "00s" => [2000, 2009],
        "2010s" => [2010, 2019], "10s" => [2010, 2019],
        "2020s" => [2020, 2029]
    ];
}
