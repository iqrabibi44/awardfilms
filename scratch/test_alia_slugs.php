<?php
require_once __DIR__ . '/../config/DB.php';
require_once __DIR__ . '/../lib/queries.php';

$res = getFilmWithNominations('alia-bhatt');
if (!$res) {
    echo "getFilmWithNominations returned null for alia-bhatt\n";
} else {
    print_r($res);
}
