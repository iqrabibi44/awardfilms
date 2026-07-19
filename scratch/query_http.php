<?php
require_once __DIR__ . '/../config/DB.php';
$pdo = DB::connection();

echo "--- NOMINATIONS WITH HTTP IN NOTE ---\n";
$stmt = $pdo->query("SELECT id, nominee_text, note, source_ref FROM nominations WHERE note LIKE '%http%' OR source_ref LIKE '%http%' LIMIT 10");
print_r($stmt->fetchAll(PDO::FETCH_ASSOC));
?>
