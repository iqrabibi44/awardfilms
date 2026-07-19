<?php
require 'lib/navigation.php';
$res = [];
foreach($NAV_DATA as $cat) {
    foreach($cat['industries'] as $ind) {
        foreach($ind['ceremonies'] as $c) {
            $res[] = $c['slug'];
        }
    }
}
print_r($res);
