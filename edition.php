<?php
require_once __DIR__ . '/lib/queries.php';
require_once __DIR__ . '/lib/navigation.php';

$supercategory = $_GET['supercategory'] ?? '';
$industry = $_GET['industry'] ?? '';
$ceremonySlug = $_GET['ceremony'] ?? '';
$detailSlug = $_GET['slug'] ?? '';

// Find category/industry/ceremony objects to validate structure
$cat = null;
foreach ($NAV_DATA as $c) {
    if ($c['slug'] === $supercategory) {
        $cat = $c;
        break;
    }
}
$ind = null;
if ($cat) {
    foreach ($cat['industries'] as $i) {
        if ($i['slug'] === $industry) {
            $ind = $i;
            break;
        }
    }
}
$cObj = null;
if ($ind) {
    foreach ($ind['ceremonies'] as $c) {
        if ($c['slug'] === $ceremonySlug) {
            $cObj = $c;
            break;
        }
    }
}

if (!$cat || !$ind || !$cObj) {
    http_response_code(404);
    echo "<h1>Path validation failed</h1>";
    exit;
}

$isYear = false;
$year = null;
if (is_numeric($detailSlug)) {
    $isYear = true;
    $year = (int)$detailSlug;
} elseif (preg_match('/-(\d{4})$/', $detailSlug, $matches)) {
    $isYear = true;
    $year = (int)$matches[1];
}

// Map the UI slug to the database generic slug for DB queries
$cRow = getCeremonyBySlug($ceremonySlug);
$dbSlug = $cRow ? $cRow['slug'] : $ceremonySlug;

if ($isYear) {
    // ─── EDITION YEAR VIEW ───
    $data = getEditionWithAllCategories($dbSlug, $year);
    if (!$data) {
        http_response_code(404);
        echo "<h1>Edition Year not found in database</h1>";
        exit;
    }

    // Best in show mock or query
    // Let's check: can we extract best in show from categories?
    // Best film is usually from category with 'Best Film' or 'Best Picture'
    $bestFilm = null;
    $mostAwardedFilm = null;
    $mostAwardedPerson = null;
    
    // Scan categories to find Best Film
    foreach ($data['categories'] as $c) {
        if (strpos(strtolower($c['name']), 'best film') !== false || strpos(strtolower($c['name']), 'best picture') !== false) {
            foreach ($c['nominations'] as $n) {
                if ($n['is_winner'] && $n['film']) {
                    $bestFilm = $n['film'];
                    break 2;
                }
            }
        }
    }
    
    // Compute most awarded film/person in this edition
    $filmWins = [];
    $personWins = [];
    foreach ($data['categories'] as $c) {
        foreach ($c['nominations'] as $n) {
            if ($n['is_winner']) {
                if ($n['film']) {
                    $title = $n['film']['title'];
                    $filmWins[$title] = ($filmWins[$title] ?? 0) + 1;
                    if (!isset($filmPosters[$title])) $filmPosters[$title] = $n['film'];
                }
                if ($n['person']) {
                    $name = $n['person']['name'];
                    $personWins[$name] = ($personWins[$name] ?? 0) + 1;
                    if (!isset($personPhotos[$name])) $personPhotos[$name] = $n['person'];
                }
            }
        }
    }
    
    if (count($filmWins) > 0) {
        arsort($filmWins);
        $topFilmName = key($filmWins);
        $mostAwardedFilm = array_merge($filmPosters[$topFilmName], ['awards_count' => $filmWins[$topFilmName]]);
    }
    if (count($personWins) > 0) {
        arsort($personWins);
        $topPersonName = key($personWins);
        $mostAwardedPerson = array_merge($personPhotos[$topPersonName], ['awards_count' => $personWins[$topPersonName]]);
    }

    // Compute Prev / Next Edition
    $ceremonyEditions = getEditionsByCeremonyId($data['edition']['id'] ? 0 : 999000); // Fetch all years
    // Actually we can query all editions for the ceremony directly:
    $pdo = DB::connection();
    $stmt = $pdo->prepare('SELECT year FROM editions WHERE ceremony_id = (SELECT id FROM ceremonies WHERE slug = ? LIMIT 1) ORDER BY year ASC');
    $stmt->execute([$dbSlug]);
    $allYears = $stmt->fetchAll(PDO::FETCH_COLUMN) ?: [];
    
    $currentIdx = array_search($year, $allYears);
    $prevYear = ($currentIdx !== false && $currentIdx > 0) ? $allYears[$currentIdx - 1] : null;
    $nextYear = ($currentIdx !== false && $currentIdx < count($allYears) - 1) ? $allYears[$currentIdx + 1] : null;

    $numLabel = $data['edition']['edition_number'] ? $data['edition']['edition_number'] . "th" : "";

    $pageTitle = $data['ceremony']['name'] . " " . $year . " â€” Winners & Nominees";
    require_once __DIR__ . '/layouts/head.php';
    require_once __DIR__ . '/layouts/header.php';
    ?>

    <div class="min-h-screen bg-[var(--ivory)] text-navy animate-fade-in">
        <!-- Hero Header -->
        <header class="px-4 md:px-10 pt-16 pb-12 border-b border-[var(--silver)]/40 bg-gradient-to-b from-[var(--ivory-deep)] to-[var(--ivory)] relative overflow-hidden text-start">
            <div class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-6 relative z-10">
                <div class="space-y-3">
                    <nav class="text-[11px] font-semibold text-[var(--navy-light)] uppercase tracking-[0.08em] flex flex-wrap items-center gap-1.5">
                        <a href="/cinema/<?php echo htmlspecialchars($supercategory); ?>" class="hover:text-navy transition-colors"><?php echo htmlspecialchars($cat['label']); ?> Cinema</a>
                        <span>â€º</span>
                        <a href="/cinema/<?php echo htmlspecialchars($supercategory); ?>/<?php echo htmlspecialchars($industry); ?>" class="hover:text-navy transition-colors"><?php echo htmlspecialchars($ind['name']); ?></a>
                        <span>â€º</span>
                        <a href="/<?php echo "$supercategory/$industry/$ceremonySlug"; ?>" class="hover:text-navy transition-colors"><?php echo htmlspecialchars($data['ceremony']['name']); ?></a>
                        <span>â€º</span>
                        <span class="text-[var(--gold)]"><?php echo $year; ?></span>
                    </nav>

                    <h1 class="font-serif text-6xl md:text-7xl lg:text-8xl font-bold leading-none text-navy">
                        <?php echo $year; ?>
                    </h1>
                    <h2 class="text-lg md:text-xl text-[var(--navy-light)] font-serif font-medium">
                        <?php echo $numLabel ? $numLabel . " " : ""; ?><?php echo htmlspecialchars($data['ceremony']['name']); ?>
                    </h2>

                    <!-- Meta row -->
                    <div class="flex flex-wrap items-center gap-4 text-xs md:text-sm text-[var(--navy-light)] font-medium pt-1">
                        <?php if ($data['edition']['date_held']): ?>
                            <span>📅 <?php echo date("F Y", strtotime($data['edition']['date_held'])); ?></span>
                        <?php endif; ?>
                        <?php if ($data['edition']['venue']): ?>
                            <span>ðŸ“ <?php echo htmlspecialchars($data['edition']['venue']); ?></span>
                        <?php endif; ?>
                        <?php if ($data['edition']['host']): ?>
                            <span>🎤 <?php echo htmlspecialchars($data['edition']['host']); ?></span>
                        <?php endif; ?>
                    </div>

                    <!-- Stats summary -->
                    <div class="flex items-center gap-6 pt-4">
                        <div>
                            <span class="font-serif text-2xl font-bold text-[var(--gold)] me-1"><?php echo $data['summary']['total_categories']; ?></span>
                            <span class="text-xs text-[var(--navy-light)] font-bold uppercase tracking-wider">Categories</span>
                        </div>
                        <div>
                            <span class="font-serif text-2xl font-bold text-[var(--gold)] me-1"><?php echo $data['summary']['total_nominations']; ?></span>
                            <span class="text-xs text-[var(--navy-light)] font-bold uppercase tracking-wider">Nominees</span>
                        </div>
                        <div>
                            <span class="font-serif text-2xl font-bold text-[var(--gold)] me-1"><?php echo $data['summary']['total_winners']; ?></span>
                            <span class="text-xs text-[var(--navy-light)] font-bold uppercase tracking-wider">Winners</span>
                        </div>
                    </div>
                </div>

                <!-- Pagination navigation buttons -->
                <div class="flex items-center gap-4 shrink-0 md:self-start md:pt-4">
                    <?php if ($prevYear): ?>
                        <a href="/<?php echo "$supercategory/$industry/$ceremonySlug/$prevYear"; ?>" class="text-xs font-bold text-[var(--navy-light)] hover:text-[var(--gold)] transition-colors border border-[var(--silver)] bg-white px-3.5 py-2 rounded-[2px] shadow-sm">
                            â† <?php echo $prevYear; ?> Edition
                        </a>
                    <?php else: ?>
                        <span class="text-xs font-bold text-gray-400 border border-[var(--silver)] bg-gray-50 px-3.5 py-2 rounded-[2px] cursor-not-allowed">â† First Ed.</span>
                    <?php endif; ?>

                    <?php if ($nextYear): ?>
                        <a href="/<?php echo "$supercategory/$industry/$ceremonySlug/$nextYear"; ?>" class="text-xs font-bold text-[var(--navy-light)] hover:text-[var(--gold)] transition-colors border border-[var(--silver)] bg-white px-3.5 py-2 rounded-[2px] shadow-sm">
                            <?php echo $nextYear; ?> Edition →
                        </a>
                    <?php else: ?>
                        <span class="text-xs font-bold text-gray-400 border border-[var(--silver)] bg-gray-50 px-3.5 py-2 rounded-[2px] cursor-not-allowed">Latest Ed. →</span>
                    <?php endif; ?>
                </div>
            </div>
        </header>

        <!-- Edition Content -->
        <main class="max-w-7xl mx-auto px-4 md:px-10 py-10 space-y-10">
            <!-- Best in show highlights -->
            <?php if ($bestFilm || $mostAwardedFilm || $mostAwardedPerson): ?>
            <section class="bg-gradient-to-br from-[var(--gold)]/5 to-transparent border border-[var(--gold)]/20 rounded-[3px] p-5 md:p-6 space-y-4 text-start">
                <div class="text-[11px] font-bold uppercase tracking-[0.12em] text-[var(--gold)] flex items-center gap-1.5">
                    <span>â­</span> Best In Show
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
                    <!-- 1. Best Film -->
                    <?php if ($bestFilm): ?>
                    <div class="flex items-center gap-4 border-e border-[var(--silver)] last:border-0 pe-4">
                        <?php if ($bestFilm['poster_url']): ?>
                            <img src="<?php echo htmlspecialchars($bestFilm['poster_url']); ?>" alt="<?php echo htmlspecialchars($bestFilm['title']); ?>" class="w-12 h-16 rounded object-cover shrink-0">
                        <?php else: ?>
                            <div class="w-12 h-16 bg-neutral-800 rounded flex items-center justify-center shrink-0 text-xl">🎬</div>
                        <?php endif; ?>
                        <div class="min-w-0">
                            <div class="text-[10px] text-[var(--navy-light)] uppercase tracking-wider font-bold">Best Film Winner</div>
                            <a href="/films/<?php echo $bestFilm['slug']; ?>" class="font-serif font-bold text-navy text-base hover:text-[var(--gold)] transition-colors truncate block mt-0.5"><?php echo htmlspecialchars($bestFilm['title']); ?></a>
                            <div class="text-[11px] text-[var(--navy-light)] mt-0.5">Top Honour</div>
                        </div>
                    </div>
                    <?php endif; ?>

                    <!-- 2. Most Awarded Film -->
                    <?php if ($mostAwardedFilm): ?>
                    <div class="flex items-center gap-4 border-e border-[var(--silver)] last:border-0 pe-4">
                        <?php if ($mostAwardedFilm['poster_url']): ?>
                            <img src="<?php echo htmlspecialchars($mostAwardedFilm['poster_url']); ?>" alt="<?php echo htmlspecialchars($mostAwardedFilm['title']); ?>" class="w-12 h-16 rounded object-cover shrink-0">
                        <?php else: ?>
                            <div class="w-12 h-16 bg-neutral-800 rounded flex items-center justify-center shrink-0 text-xl">🎬</div>
                        <?php endif; ?>
                        <div class="min-w-0">
                            <div class="text-[10px] text-[var(--navy-light)] uppercase tracking-wider font-bold">Most Awarded Film</div>
                            <a href="/films/<?php echo $mostAwardedFilm['slug']; ?>" class="font-serif font-bold text-navy text-base hover:text-[var(--gold)] transition-colors truncate block mt-0.5"><?php echo htmlspecialchars($mostAwardedFilm['title']); ?></a>
                            <div class="text-xs text-[var(--gold)] font-bold mt-1">ðŸ† <?php echo $mostAwardedFilm['awards_count']; ?> awards</div>
                        </div>
                    </div>
                    <?php endif; ?>

                    <!-- 3. Most Awarded Person -->
                    <?php if ($mostAwardedPerson): ?>
                    <div class="flex items-center gap-4 pe-4">
                        <?php if ($mostAwardedPerson['photo_url']): ?>
                            <img src="<?php echo htmlspecialchars($mostAwardedPerson['photo_url']); ?>" alt="<?php echo htmlspecialchars($mostAwardedPerson['name']); ?>" class="w-12 h-12 rounded-full object-cover shrink-0">
                        <?php else: ?>
                            <div class="w-12 h-12 bg-neutral-800 rounded-full flex items-center justify-center shrink-0 text-xl">👤</div>
                        <?php endif; ?>
                        <div class="min-w-0">
                            <div class="text-[10px] text-[var(--navy-light)] uppercase tracking-wider font-bold">Most Awarded Person</div>
                            <a href="/persons/<?php echo $mostAwardedPerson['slug']; ?>" class="font-serif font-bold text-navy text-base hover:text-[var(--gold)] transition-colors truncate block mt-0.5"><?php echo htmlspecialchars($mostAwardedPerson['name']); ?></a>
                            <div class="text-xs text-[var(--gold)] font-bold mt-1">ðŸ† <?php echo $mostAwardedPerson['awards_count']; ?> awards</div>
                        </div>
                    </div>
                    <?php endif; ?>
                </div>
            </section>
            <?php endif; ?>

            <!-- Categories and nominations list -->
            <section class="space-y-6 text-start" x-data="{ activeTab: 'All Categories' }">
                <!-- Tab filter header -->
                <div class="border-b border-[var(--silver)]/40 flex gap-2 overflow-x-auto scrollbar-none pb-0.5 sticky top-[60px] z-30 bg-[var(--ivory)] py-2">
                    <?php 
                    $tabs = ["All Categories", "Film", "Direction", "Performance", "Music", "Technical"];
                    foreach ($tabs as $t):
                    ?>
                    <button @click="activeTab = '<?php echo $t; ?>'"
                            :class="activeTab === '<?php echo $t; ?>' ? 'border-[var(--gold)] text-navy' : 'border-transparent text-[var(--navy-light)] hover:text-navy'"
                            class="px-4 py-2 text-xs font-bold border-b-2 transition-all cursor-pointer whitespace-nowrap">
                        <?php echo $t; ?>
                    </button>
                    <?php endforeach; ?>
                </div>

                <!-- Grid of category cards -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <?php 
                    foreach ($data['categories'] as $c): 
                        // Separate winner & nominees
                        $winner = null;
                        $nominees = [];
                        foreach ($c['nominations'] as $n) {
                            if ($n['is_winner']) {
                                $winner = $n;
                            } else {
                                $nominees[] = $n;
                            }
                        }
                        if (!$winner && count($c['nominations']) > 0) {
                            $winner = $c['nominations'][0];
                            $nominees = array_slice($c['nominations'], 1);
                        }
                    ?>
                    <!-- Category card wrapping Alpine layout matching Department tabs -->
                    <div class="card-royal p-0 flex flex-col justify-between"
                         x-show="activeTab === 'All Categories' || 
                                 (activeTab === 'Film' && ('<?php echo strtolower($c['department']); ?>'.includes('film') || '<?php echo strtolower($c['name']); ?>'.includes('best film') || '<?php echo strtolower($c['name']); ?>'.includes('best picture'))) ||
                                 (activeTab === 'Direction' && ('<?php echo strtolower($c['department']); ?>'.includes('direction') || '<?php echo strtolower($c['name']); ?>'.includes('director'))) ||
                                 (activeTab === 'Performance' && ('<?php echo strtolower($c['department']); ?>'.includes('performance') || '<?php echo strtolower($c['department']); ?>'.includes('acting') || '<?php echo strtolower($c['department']); ?>'.includes('actor') || '<?php echo strtolower($c['department']); ?>'.includes('actress'))) ||
                                 (activeTab === 'Music' && ('<?php echo strtolower($c['department']); ?>'.includes('music') || '<?php echo strtolower($c['department']); ?>'.includes('song'))) ||
                                 (activeTab === 'Technical' && ('<?php echo strtolower($c['department']); ?>'.includes('technical') || '<?php echo strtolower($c['department']); ?>'.includes('craft') || '<?php echo strtolower($c['department']); ?>'.includes('camera') || '<?php echo strtolower($c['department']); ?>'.includes('editing') || '<?php echo strtolower($c['department']); ?>'.includes('writing') || '<?php echo strtolower($c['department']); ?>'.includes('sound')))">
                        
                        <div class="bg-[rgba(27,42,74,0.02)] border-b border-[var(--silver)]/40 px-4 py-3 flex justify-between items-center gap-3">
                            <span class="text-[12px] uppercase tracking-[0.08em] font-bold text-[var(--navy-light)] truncate"><?php echo htmlspecialchars($c['name']); ?></span>
                            <span class="text-[10px] text-[var(--navy-light)] bg-navy/5 border border-[var(--silver)] px-2 py-0.5 rounded-[2px]"><?php echo htmlspecialchars($c['department']); ?></span>
                        </div>

                        <!-- Winner element -->
                        <?php if ($winner): ?>
                        <div class="bg-[var(--gold)]/5 border-s-[3px] border-s-[var(--gold)] px-4 py-3.5 flex items-center justify-between group">
                            <div class="flex items-center gap-3">
                                <?php 
                                $imageUrl = $winner['film']['poster_url'] ?? ($winner['person']['photo_url'] ?? null); 
                                if ($imageUrl):
                                ?>
                                    <img src="<?php echo htmlspecialchars($imageUrl); ?>" class="w-9 h-12 object-cover bg-neutral-800 rounded shrink-0">
                                <?php else: ?>
                                    <div class="w-9 h-12 bg-neutral-800 rounded flex items-center justify-center shrink-0 text-sm">🎬</div>
                                <?php endif; ?>
                                <div class="text-start">
                                    <div class="text-[9px] text-[var(--gold)] font-bold tracking-widest uppercase">ðŸ† WINNER</div>
                                    <div class="font-bold text-navy text-sm truncate"><?php echo htmlspecialchars($winner['person']['name'] ?? $winner['nominee_text']); ?></div>
                                    <?php if ($winner['film']): ?>
                                        <div class="text-xs text-[var(--navy-light)] truncate mt-0.5"><?php echo htmlspecialchars($winner['film']['title']); ?></div>
                                    <?php endif; ?>
                                </div>
                            </div>
                            <?php 
                            $slugUrl = $winner['film'] ? '/films/' . $winner['film']['slug'] : ($winner['person'] ? '/persons/' . $winner['person']['slug'] : null);
                            if ($slugUrl):
                            ?>
                                <a href="<?php echo $slugUrl; ?>" class="text-[var(--navy-light)] hover:text-[var(--gold)] font-bold transition-colors text-sm">&rarr;</a>
                            <?php endif; ?>
                        </div>
                        <?php endif; ?>

                        <!-- Nominees Toggle list (mobile or expandable) -->
                        <?php if (count($nominees) > 0): ?>
                        <div class="border-t border-[var(--silver)]/40 p-4 space-y-3">
                            <div class="text-[10px] text-[var(--navy-light)] uppercase tracking-wider font-bold mb-2">Other Nominees</div>
                            <div class="space-y-2">
                                <?php foreach ($nominees as $nom): ?>
                                <div class="flex justify-between items-center text-xs gap-3">
                                    <div class="flex items-center gap-2">
                                        <span class="text-gray-400">&bull;</span>
                                        <span class="font-semibold text-navy"><?php echo htmlspecialchars($nom['person']['name'] ?? $nom['nominee_text']); ?></span>
                                        <?php if ($nom['film'] && ($nom['film']['title'] !== $nom['nominee_text'])): ?>
                                            <span class="text-[var(--navy-light)]">&mdash; <?php echo htmlspecialchars($nom['film']['title']); ?></span>
                                        <?php endif; ?>
                                    </div>
                                    <?php 
                                    $nUrl = $nom['film'] ? '/films/' . $nom['film']['slug'] : ($nom['person'] ? '/persons/' . $nom['person']['slug'] : null);
                                    if ($nUrl):
                                    ?>
                                        <a href="<?php echo $nUrl; ?>" class="text-[var(--navy-light)] hover:text-[var(--gold)] font-bold">&rarr;</a>
                                    <?php endif; ?>
                                </div>
                                <?php endforeach; ?>
                            </div>
                        </div>
                        <?php endif; ?>

                    </div>
                    <?php endforeach; ?>
                </div>
            </section>
        </main>
    </div>

    <?php
} else {
    // ─── CATEGORY ARCHIVE VIEW ───
    $categorySlug = $detailSlug;
    $data = getCategoryAllWinners($dbSlug, $categorySlug);
    if (!$data) {
        http_response_code(404);
        $pageTitle = "Category Archive Not Found";
        require_once __DIR__ . '/layouts/head.php';
        require_once __DIR__ . '/layouts/header.php';
        echo '<div class="min-h-screen bg-[var(--ivory)] text-navy pt-32 pb-12 px-6 flex flex-col items-center justify-center animate-fade-in">';
        
        // TEMPORARY DEBUG OUTPUT
        echo '<div style="background: #fee2e2; border: 1px solid #f87171; padding: 15px; margin-bottom: 20px; border-radius: 5px; font-family: monospace; text-align: left; max-width: 600px; width: 100%; color: #991b1b;">';
        echo '<strong>[DEBUG INFO]</strong><br>';
        echo 'URL Slug (incoming category): ' . htmlspecialchars($categorySlug) . '<br>';
        
        try {
            $pdo = DB::connection();
            // Let's first find ceremony id
            $stmtC = $pdo->prepare('SELECT id FROM ceremonies WHERE slug = ? LIMIT 1');
            $stmtC->execute([$dbSlug]);
            $cId = $stmtC->fetchColumn();
            
            $clean = str_replace(['best-', '-award', '-awards'], '', $categorySlug);
            $searchTerm = '%' . str_replace('-', '%', $clean) . '%';
            
            if ($cId) {
                $stmt = $pdo->prepare('SELECT slug, name FROM categories WHERE ceremony_id = ? AND (slug LIKE ? OR name LIKE ? OR slug LIKE ?) LIMIT 5');
                $stmt->execute([$cId, $searchTerm, $searchTerm, '%' . $categorySlug . '%']);
                $matches = $stmt->fetchAll();
                if ($matches) {
                    echo 'Closest DB category matches for this ceremony:<br>';
                    foreach ($matches as $m) {
                        echo '- Slug in DB: <strong>' . htmlspecialchars($m['slug']) . '</strong> | Name: ' . htmlspecialchars($m['name']) . '<br>';
                    }
                } else {
                    echo 'No similar categories found in DB for this ceremony.<br>';
                }
            } else {
                echo 'Ceremony not found in DB.<br>';
            }
        } catch (Exception $e) {
            echo 'Error querying DB: ' . htmlspecialchars($e->getMessage()) . '<br>';
        }
        echo '</div>';
        
        echo '<h1 class="font-serif text-[32px] md:text-[40px] text-navy mb-4">' . __('Archive Not Found') . '</h1>';
        echo '<p class="text-[var(--silver)] font-sans text-[15px] tracking-wide mb-8">' . __('This category archive isn\'t available yet.') . '</p>';
        echo '<a href="/browse" class="inline-block px-8 py-3 bg-navy text-[var(--ivory)] rounded hover:bg-[var(--gold)] transition-colors uppercase tracking-[2px] text-[12px] font-bold">' . __('Browse Categories') . '</a>';
        echo '</div>';
        require_once __DIR__ . '/layouts/footer.php';
        exit;
    }

    $totalWinners = count($data['winners']);
    $pageTitle = $data['ceremony']['name'] . " for " . $data['category']['name'] . " â€” All Winners";
    require_once __DIR__ . '/layouts/head.php';
    require_once __DIR__ . '/layouts/header.php';
    ?>

    <div class="min-h-screen bg-[var(--ivory)] text-navy animate-fade-in text-start">
        <!-- Hero Header -->
        <header class="px-4 md:px-10 pt-16 pb-12 border-b border-[var(--silver)]/40 bg-gradient-to-b from-[var(--ivory-deep)] to-[var(--ivory)] relative">
            <div class="max-w-7xl mx-auto space-y-4">
                <nav class="text-[11px] font-semibold text-[var(--navy-light)] uppercase tracking-[0.08em] flex flex-wrap items-center gap-1.5">
                    <a href="/cinema/<?php echo htmlspecialchars($supercategory); ?>" class="hover:text-navy transition-colors"><?php echo htmlspecialchars($cat['label']); ?> Cinema</a>
                    <span>â€º</span>
                    <a href="/cinema/<?php echo htmlspecialchars($supercategory); ?>/<?php echo htmlspecialchars($industry); ?>" class="hover:text-navy transition-colors"><?php echo htmlspecialchars($ind['name']); ?></a>
                    <span>â€º</span>
                    <a href="/<?php echo "$supercategory/$industry/$ceremonySlug"; ?>" class="hover:text-navy transition-colors"><?php echo htmlspecialchars($data['ceremony']['name']); ?></a>
                    <span>â€º</span>
                    <span class="text-[var(--gold)]"><?php echo htmlspecialchars($data['category']['name']); ?></span>
                </nav>

                <p class="text-[11px] font-bold tracking-widest text-[var(--gold)] uppercase">
                    <?php echo htmlspecialchars($data['category']['department']); ?> Category Archive
                </p>

                <h1 class="font-serif text-4xl md:text-5xl font-bold leading-tight">
                    <?php echo htmlspecialchars($data['category']['name']); ?> winners
                </h1>

                <div class="flex items-center gap-3 text-xs text-[var(--navy-light)]">
                    <span><?php echo htmlspecialchars($data['ceremony']['name']); ?> Records</span>
                    <span>â€¢</span>
                    <span><?php echo $totalWinners; ?> historical winners</span>
                </div>
            </div>
        </header>

        <!-- Category winners history grid -->
        <main class="max-w-7xl mx-auto px-4 md:px-10 py-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div class="lg:col-span-8 space-y-6">
                <!-- Table of winners -->
                <div class="card-royal p-0 bg-white">
                    <div class="overflow-x-auto">
                        <table class="w-full text-start text-xs font-sans">
                            <thead class="bg-gray-50 border-b border-[var(--silver)]/45 text-[10px] text-[var(--navy-light)] uppercase font-bold tracking-wider">
                                <tr>
                                    <th class="px-6 py-3.5">Year</th>
                                    <th class="px-6 py-3.5">Winner</th>
                                    <th class="px-6 py-3.5">Film / Note</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-[var(--silver)]/20">
                                <?php foreach ($data['winners'] as $w): ?>
                                <tr class="hover:bg-gray-50 transition-colors">
                                    <td class="px-6 py-4 font-serif text-base font-bold text-[var(--gold)]">
                                        <a href="/<?php echo "$supercategory/$industry/$ceremonySlug/"; ?><?php echo $w['year']; ?>" class="hover:underline">
                                            <?php echo $w['year']; ?>
                                        </a>
                                    </td>
                                    <td class="px-6 py-4 font-semibold text-navy">
                                        <?php if ($w['person']): ?>
                                            <a href="/persons/<?php echo $w['person']['slug']; ?>" class="hover:text-[var(--gold)] transition-colors">
                                                <?php echo htmlspecialchars($w['person']['name']); ?>
                                            </a>
                                        <?php else: ?>
                                            <?php echo htmlspecialchars($w['nominee_text']); ?>
                                        <?php endif; ?>
                                    </td>
                                    <td class="px-6 py-4 text-[var(--navy-light)]">
                                        <?php if ($w['film']): ?>
                                            <a href="/films/<?php echo $w['film']['slug']; ?>" class="font-serif italic hover:text-[var(--gold)] transition-colors">
                                                <?php echo htmlspecialchars($w['film']['title']); ?>
                                            </a>
                                        <?php else: ?>
                                            <span class="text-gray-400">&mdash;</span>
                                        <?php endif; ?>
                                    </td>
                                </tr>
                                <?php endforeach; ?>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Stats Sidebar -->
            <aside class="lg:col-span-4 bg-[var(--ivory-card)] border border-[var(--silver)] rounded-[3px] p-5 space-y-6 shadow-[0_4px_24px_var(--shadow)]">
                <h3 class="text-xs font-bold text-[var(--navy-light)] uppercase tracking-wider border-b border-[var(--silver)]/40 pb-2 mb-4">Category Records</h3>
                <div class="space-y-4 text-xs text-[var(--navy-light)]">
                    <div>
                        <div class="uppercase tracking-wider font-bold text-[10px]">Total Winners Archived</div>
                        <div class="font-serif text-2xl font-bold text-navy mt-1"><?php echo $totalWinners; ?></div>
                    </div>
                    <?php if ($totalWinners > 0): ?>
                    <div class="border-t border-[var(--silver)]/40 pt-3">
                        <div class="uppercase tracking-wider font-bold text-[10px]">Latest Recipient</div>
                        <div class="font-serif text-base font-bold text-navy mt-1">
                            <?php 
                            $latest = $data['winners'][0];
                            echo htmlspecialchars($latest['person']['name'] ?? ($latest['film']['title'] ?? $latest['nominee_text'])); 
                            ?>
                        </div>
                        <div class="text-[10px] mt-0.5">Year: <?php echo $latest['year']; ?></div>
                    </div>
                    <div class="border-t border-[var(--silver)]/40 pt-3">
                        <div class="uppercase tracking-wider font-bold text-[10px]">Inaugural Winner</div>
                        <div class="font-serif text-base font-bold text-navy mt-1">
                            <?php 
                            $first = $data['winners'][$totalWinners - 1];
                            echo htmlspecialchars($first['person']['name'] ?? ($first['film']['title'] ?? $first['nominee_text'])); 
                            ?>
                        </div>
                        <div class="text-[10px] mt-0.5">Year: <?php echo $first['year']; ?></div>
                    </div>
                    <?php endif; ?>
                </div>
            </aside>
        </main>
    </div>

    <?php
}

require_once __DIR__ . '/layouts/footer.php';
?>

