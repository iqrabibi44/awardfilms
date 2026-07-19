<?php
require_once __DIR__ . '/../config/DB.php';

header('Content-Type: application/json');
$pdo = DB::connection();

$diagnostics = [];

// 1. Test ceremony lookup
$targetSlug = 'oscars';
$stmt = $pdo->prepare("SELECT * FROM ceremonies WHERE slug = ?");
$stmt->execute([$targetSlug]);
$diagnostics['lookup_ceremony_oscars'] = $stmt->fetch() ?: 'Not found';

// What ceremonies are in DB?
$stmt = $pdo->query("SELECT id, name, slug FROM ceremonies LIMIT 10");
$diagnostics['some_ceremonies_in_db'] = $stmt->fetchAll();

// 2. Search for oscars by name
$stmt = $pdo->query("SELECT id, name, slug FROM ceremonies WHERE name LIKE '%oscar%' OR name LIKE '%academy%'");
$diagnostics['search_oscars_by_name'] = $stmt->fetchAll();

// 3. Test category lookup
$targetCategorySlug = 'best-picture';
$stmt = $pdo->prepare("SELECT id, name, slug FROM categories WHERE slug = ?");
$stmt->execute([$targetCategorySlug]);
$diagnostics['lookup_category_best-picture'] = $stmt->fetch() ?: 'Not found';

// 4. Search for category by name
$stmt = $pdo->query("SELECT id, name, slug FROM categories WHERE name LIKE '%best picture%' OR name LIKE '%mejor%' LIMIT 5");
$diagnostics['search_category_best_picture_by_name'] = $stmt->fetchAll();

// 5. Persons
$stmt = $pdo->prepare("SELECT id, name, slug FROM persons WHERE slug = 'alia-bhatt'");
$stmt->execute();
$diagnostics['lookup_person_alia-bhatt'] = $stmt->fetch() ?: 'Not found';

$stmt = $pdo->query("SELECT id, name, slug FROM persons WHERE name LIKE '%alia bhatt%'");
$diagnostics['search_person_alia_bhatt'] = $stmt->fetchAll();

echo json_encode($diagnostics, JSON_PRETTY_PRINT);
