<?php
// lib/queryParser.php
require_once __DIR__ . '/searchAliases.php';
require_once __DIR__ . '/searchIntents.php';

function parseQuery($raw) {
    // 1. Lowercase + trim
    $text = strtolower(trim($raw));
    
    // Normalize nicknames to avoid duplicates
    $text = str_replace('shah rukh khan', 'srk', $text);
    $text = str_replace('shahrukh khan', 'srk', $text);
    $text = str_replace('shahrukh', 'srk', $text);
    $text = str_replace('shah rukh', 'srk', $text);
    $text = str_replace('amitabh bachchan', 'big b', $text);
    $text = str_replace('salman khan', 'bhai', $text);
    $text = str_replace('aamir khan', 'aamir', $text);
    $text = str_replace('alia bhatt', 'alia', $text);
    $text = str_replace('aliya bhat', 'alia', $text);
    $text = str_replace('aliya', 'alia', $text);

    $nicknameMap = [
        'srk' => 'shah rukh khan',
        'king khan' => 'shah rukh khan',
        'big b' => 'amitabh bachchan',
        'bhai' => 'salman khan',
        'mr perfectionist' => 'aamir khan',
        'aamir' => 'aamir khan',
        'alia' => 'alia bhatt'
    ];
    foreach ($nicknameMap as $nick => $full) {
        $pattern = '/\b' . preg_quote($nick, '/') . '\b/';
        if (preg_match($pattern, $text)) {
            $text = preg_replace($pattern, $full, $text);
        }
    }
    
    $result = [
        'person' => null,
        'film' => null,
        'ceremony' => null,
        'category' => null,
        'year' => null,
        'yearRange' => null,
        'onlyWinners' => null,
        'resultType' => 'mixed',
        'leftoverText' => ''
    ];

    if (empty($text)) {
        return $result;
    }

    // Load aliases
    $aliases = SearchAliases::getAliases();

    // 2. Extract 4-digit year: /\b(19[5-9]\d|20[0-2]\d)\b/
    if (preg_match('/\b(19[5-9]\d|20[0-2]\d)\b/', $text, $matches)) {
        $result['year'] = (int)$matches[1];
        $text = trim(preg_replace('/\b' . $matches[1] . '\b/', '', $text));
    }

    // 3. Decade keywords -> yearRange
    foreach (SearchIntents::$decadeMap as $decadeKey => $range) {
        $pattern = '/\b' . preg_quote($decadeKey, '/') . '\b/';
        if (preg_match($pattern, $text)) {
            $result['yearRange'] = $range;
            $text = trim(preg_replace($pattern, '', $text));
            break; 
        }
    }

    // 4. Match CATEGORY_WORDS before stripping general terms
    $categoriesSorted = [];
    foreach (SearchIntents::$categoryWords as $categoryName => $synonyms) {
        foreach ($synonyms as $syn) {
            $categoriesSorted[$syn] = $categoryName;
        }
    }
    uksort($categoriesSorted, function($a, $b) {
        return strlen($b) - strlen($a);
    });

    foreach ($categoriesSorted as $syn => $categoryName) {
        $pattern = '/\b' . preg_quote($syn, '/') . '\b/';
        if (preg_match($pattern, $text)) {
            $result['category'] = $categoryName;
            $text = trim(preg_replace($pattern, '', $text));
            break;
        }
    }

    // 5. Match CEREMONY_ALIASES
    uksort($aliases['ceremonies'], function($a, $b) {
        return strlen($b) - strlen($a);
    });
    foreach ($aliases['ceremonies'] as $alias => $cData) {
        $pattern = '/\b' . preg_quote($alias, '/') . '\b/';
        if (preg_match($pattern, $text)) {
            $result['ceremony'] = $cData;
            $text = trim(preg_replace($pattern, '', $text));
            break;
        }
    }

    // 6. Match INTENT/STOP words using token-based fuzzy checking
    $words = explode(' ', $text);
    $keptWords = [];
    $stopWords = [
        'awards', 'award', 'movie', 'movies', 'film', 'films', 
        'for', 'which', 'the', 'of', 'in', 'and', 'who', 'a', 'an'
    ];
    
    foreach ($words as $word) {
        $word = trim($word);
        if (empty($word)) continue;
        
        if (matchFuzzyWord($word, SearchIntents::$winnerWords, 2)) {
            $result['onlyWinners'] = true;
            continue;
        }
        if (matchFuzzyWord($word, SearchIntents::$nomineeWords, 2)) {
            $result['onlyWinners'] = false;
            continue;
        }
        if (matchFuzzyWord($word, $stopWords, 2)) {
            continue;
        }
        $keptWords[] = $word;
    }
    
    $text = implode(' ', $keptWords);
    $text = preg_replace('/\s+/', ' ', $text);
    $text = trim($text);

    // 8. Look up the remaining text in personAliases or filmAliases
    if (!empty($text)) {
        if (isset($aliases['persons'][$text])) {
            $result['person'] = $aliases['persons'][$text];
            $text = '';
        } else {
            // Check if there is any person alias that starts with the text as a word boundary
            foreach ($aliases['persons'] as $aliasName => $pData) {
                if (strpos($aliasName, $text) === 0) {
                    $result['person'] = $pData;
                    $text = '';
                    break;
                }
            }
        }
    }

    if (!empty($text)) {
        // Try exact match in film index
        foreach ($aliases['films'] as $f) {
            if (strtolower($f['title']) === $text) {
                $result['film'] = $f;
                $text = '';
                break;
            }
        }
    }

    // 9. Tight fuzzy matching ONLY when exact matching didn't yield anything
    if (!empty($text) && strlen($text) >= 3) {
        $bestPerson = null;
        $highestPersonSim = 0;
        foreach ($aliases['persons'] as $aliasName => $pData) {
            $lev = levenshtein($text, $aliasName);
            if ($lev <= 2) {
                $maxLen = max(strlen($text), strlen($aliasName));
                if ($maxLen > 0) {
                    $sim = (1 - ($lev / $maxLen)) * 100;
                    if ($sim >= 85 && $sim > $highestPersonSim) {
                        $highestPersonSim = $sim;
                        $bestPerson = $pData;
                    }
                }
            }
        }
        if ($bestPerson) {
            $result['person'] = $bestPerson;
            $text = '';
        }
    }

    if (!empty($text) && strlen($text) >= 3) {
        $bestFilm = null;
        $highestFilmSim = 0;
        foreach ($aliases['films'] as $f) {
            $fTitle = strtolower($f['title']);
            $lev = levenshtein($text, $fTitle);
            if ($lev <= 2) {
                $maxLen = max(strlen($text), strlen($fTitle));
                if ($maxLen > 0) {
                    $sim = (1 - ($lev / $maxLen)) * 100;
                    if ($sim >= 85 && $sim > $highestFilmSim) {
                        $highestFilmSim = $sim;
                        $bestFilm = $f;
                    }
                }
            }
        }
        if ($bestFilm) {
            $result['film'] = $bestFilm;
            $text = '';
        }
    }

    $result['leftoverText'] = $text;
    return $result;
}

function getCharOverlapPercent($word1, $word2) {
    $chars1 = str_split($word1);
    $chars2 = str_split($word2);
    
    $common = 0;
    $tempChars2 = $chars2;
    foreach ($chars1 as $c) {
        $idx = array_search($c, $tempChars2);
        if ($idx !== false) {
            $common++;
            unset($tempChars2[$idx]);
        }
    }
    
    return count($chars1) > 0 ? $common / count($chars1) : 0;
}

function matchFuzzyWord($word, $targets, $maxDistance = 2) {
    $word = trim(strtolower($word));
    if (empty($word)) return null;

    foreach ($targets as $target) {
        $lev = levenshtein($word, $target);
        if ($lev <= $maxDistance) {
            $overlap = getCharOverlapPercent($word, $target);
            if ($overlap >= 0.7) {
                return $target;
            }
        }
    }
    return null;
}
