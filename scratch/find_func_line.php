<?php
require 'lib/queries.php';
$refl = new ReflectionFunction('getCategoryAllWinners');
echo $refl->getStartLine();
