<?php
$_SERVER['REQUEST_URI'] = '/browse';
ob_start();
include 'router.php';
$output = ob_get_clean();
echo "URI: /browse\n";
echo "Headers sent: " . var_export(headers_list(), true) . "\n";
echo "Output length: " . strlen($output) . "\n";
echo "Output snippet: " . substr($output, 0, 500) . "\n";
?>
