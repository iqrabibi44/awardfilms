<?php
$mappings = [
    '🏆' => '🏆',
    '🎬' => '🎬',
    '📅' => '📅',
    '👤' => '👤',
    '📍' => '📍',
    '🎤' => '🎤',
    '🎭' => '🎭',
    '🌍' => '🌍'
];

$dir = new RecursiveDirectoryIterator(__DIR__ . '/../');
$ite = new RecursiveIteratorIterator($dir);
$files = new RegexIterator($ite, '/.*\.php$/');

foreach ($files as $file) {
    $path = $file->getPathname();
    $content = file_get_contents($path);
    $newContent = strtr($content, $mappings);
    if ($newContent !== $content) {
        file_put_contents($path, $newContent);
        echo "Fixed: $path\n";
    }
}
