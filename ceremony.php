<?php
require_once __DIR__ . '/lib/queries.php';
require_once __DIR__ . '/lib/navigation.php';

$supercategory = $_GET['supercategory'] ?? '';
$industry = $_GET['industry'] ?? '';
$slug = $_GET['ceremony'] ?? '';

$ceremony = getCeremonyBySlug($slug);
if (!$ceremony) {
    http_response_code(404);
    $pageTitle = "Ceremony Not Found";
    require_once __DIR__ . '/layouts/head.php';
    require_once __DIR__ . '/layouts/header.php';
    echo '<div class="min-h-screen bg-[var(--ivory)] text-navy pt-32 pb-12 px-6 flex flex-col items-center justify-center animate-fade-in">';
    
    // TEMPORARY DEBUG OUTPUT
    echo '<div style="background: #fee2e2; border: 1px solid #f87171; padding: 15px; margin-bottom: 20px; border-radius: 5px; font-family: monospace; text-align: left; max-width: 600px; width: 100%; color: #991b1b;">';
    echo '<strong>[DEBUG INFO]</strong><br>';
    echo 'URL Slug (incoming): ' . htmlspecialchars($slug) . '<br>';
    
    try {
        $pdo = DB::connection();
        $clean = str_replace(['-awards', '-film-festival', '-prize'], '', $slug);
        $searchTerm = '%' . str_replace('-', '%', $clean) . '%';
        $stmt = $pdo->prepare('SELECT slug, name FROM ceremonies WHERE slug LIKE ? OR name LIKE ? LIMIT 5');
        $stmt->execute([$searchTerm, $searchTerm]);
        $matches = $stmt->fetchAll();
        if ($matches) {
            echo 'Closest DB matches:<br>';
            foreach ($matches as $m) {
                echo '- Slug in DB: <strong>' . htmlspecialchars($m['slug']) . '</strong> | Name: ' . htmlspecialchars($m['name']) . '<br>';
            }
        } else {
            echo 'No similar ceremonies found in DB.<br>';
        }
    } catch (Exception $e) {
        echo 'Error querying DB: ' . htmlspecialchars($e->getMessage()) . '<br>';
    }
    echo '</div>';
    
    echo '<h1 class="font-serif text-[32px] md:text-[40px] text-navy mb-4">' . __('Ceremony Not Found') . '</h1>';
    echo '<p class="text-[var(--silver)] font-sans text-[15px] tracking-wide mb-8">' . __('No records found for this ceremony yet.') . '</p>';
    echo '<a href="/browse" class="inline-block px-8 py-3 bg-navy text-[var(--ivory)] rounded hover:bg-[var(--gold)] transition-colors uppercase tracking-[2px] text-[12px] font-bold">' . __('Browse Ceremonies') . '</a>';
    echo '</div>';
    require_once __DIR__ . '/layouts/footer.php';
    exit;
}

$editionsRaw = getEditionsByCeremonyId($ceremony['id']);
$records = getCeremonyRecords($slug);
$totalEditions = count($editionsRaw);
$yearSpan = $totalEditions > 0
    ? $editionsRaw[$totalEditions - 1]['year'] . '–' . $editionsRaw[0]['year']
    : 'Est. ' . ($ceremony['founded_year'] ?: 1929);

$decadesSet = [];
foreach ($editionsRaw as $e) {
    $dec = (floor($e['year'] / 10) * 10) . 's';
    if (!in_array($dec, $decadesSet)) {
        $decadesSet[] = $dec;
    }
}
usort($decadesSet, fn($a, $b) => strcmp($b, $a));

$editions = [];
$pdo = DB::connection();

$editionIds = array_column($editionsRaw, 'id');
$countsMap = [];
$highlightsMap = [];

if (!empty($editionIds)) {
    $placeholders = implode(',', array_fill(0, count($editionIds), '?'));
    
    // Query 1: Get counts for all editions
    $stmt = $pdo->prepare("
        SELECT edition_id,
               COUNT(DISTINCT category_id) AS total_categories,
               COUNT(*) AS total_nominations,
               COUNT(CASE WHEN is_winner = 1 THEN 1 END) AS total_winners
        FROM nominations
        WHERE edition_id IN ($placeholders)
        GROUP BY edition_id
    ");
    $stmt->execute($editionIds);
    while ($row = $stmt->fetch()) {
        $countsMap[$row['edition_id']] = $row;
    }
    
    // Query 2: Get all winners to select highlights
    $stmt = $pdo->prepare("
        SELECT n.edition_id, cat.name AS category_name, f.title AS film_title, p.name AS person_name, n.nominee_text
        FROM nominations n
        INNER JOIN categories cat ON n.category_id = cat.id
        LEFT JOIN films f ON n.film_id = f.id
        LEFT JOIN persons p ON n.person_id = p.id
        WHERE n.edition_id IN ($placeholders) AND n.is_winner = 1
    ");
    $stmt->execute($editionIds);
    $allWinners = $stmt->fetchAll();
    
    // Group and sort winners in PHP to pick top 3
    $groupedWinners = [];
    foreach ($allWinners as $w) {
        $groupedWinners[$w['edition_id']][] = $w;
    }
    
    // Priority mapping helper
    $getCategoryPriority = function($name) {
        $nameLower = strtolower($name);
        if (strpos($nameLower, 'picture') !== false || 
            strpos($nameLower, 'film') !== false || 
            strpos($nameLower, 'película') !== false) {
            return 1;
        }
        if (strpos($nameLower, 'actor') !== false || 
            strpos($nameLower, 'actress') !== false || 
            strpos($nameLower, 'actriz') !== false || 
            strpos($nameLower, 'performance') !== false || 
            strpos($nameLower, 'interpr') !== false) {
            return 2;
        }
        if (strpos($nameLower, 'director') !== false || 
            strpos($nameLower, 'directing') !== false || 
            strpos($nameLower, 'dirección') !== false) {
            return 3;
        }
        return 4;
    };
    
    foreach ($groupedWinners as $eId => $winnersList) {
        usort($winnersList, function($a, $b) use ($getCategoryPriority) {
            $pA = $getCategoryPriority($a['category_name']);
            $pB = $getCategoryPriority($b['category_name']);
            if ($pA !== $pB) {
                return $pA <=> $pB;
            }
            return strcasecmp($a['category_name'], $b['category_name']);
        });
        $highlightsMap[$eId] = array_slice($winnersList, 0, 3);
    }
}

foreach ($editionsRaw as $e) {
    $counts = $countsMap[$e['id']] ?? [
        'total_categories' => 0,
        'total_nominations' => 0,
        'total_winners' => 0
    ];
    $winners = $highlightsMap[$e['id']] ?? [];

    $editions[] = [
        'id' => $e['id'],
        'year' => (int)$e['year'],
        'edition_number' => $e['edition_number'],
        'venue' => $e['venue'],
        'host' => $e['host'],
        'broadcast_network' => $e['broadcast_network'],
        'slug' => $e['slug'],
        'total_categories' => (int)($counts['total_categories'] ?? 0),
        'total_winners' => (int)($counts['total_winners'] ?? 0),
        'highlight_winners' => array_map(function($w) {
            $catLower = strtolower($w['category_name']);
            $personKeywords = ['actor', 'actress', 'director', 'singer', 'lyricist', 'writer', 'music', 'performance', 'face', 'debut', 'screenplay', 'story', 'lyrics', 'choreographer', 'cinematographer', 'editor', 'sound', 'composer', 'comedy', 'villain', 'jodi', 'pair', 'comedian', 'person', 'male', 'female', 'host'];
            $isPersonCat = false;
            foreach ($personKeywords as $kw) {
                if (strpos($catLower, $kw) !== false) {
                    $isPersonCat = true;
                    break;
                }
            }
            
            $personName = $w['person_name'] ?: ($w['nominee_text'] ?: '');
            $filmTitle = $w['film_title'] ?: '';
            
            if ($isPersonCat) {
                $displayText = $personName;
                if ($filmTitle && strtolower($filmTitle) !== strtolower($personName)) {
                    $displayText .= " ($filmTitle)";
                }
            } else {
                $displayText = $filmTitle ?: $personName;
            }
            
            return [
                'category_name' => $w['category_name'],
                'display_text' => $displayText ?: 'Winner'
            ];
        }, $winners)
    ];
}

$pageTitle = $ceremony['name'] . ' Awards Archive';
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';
?>

<div class="min-h-screen bg-[var(--ivory)] text-navy animate-fade-in text-start">

    <!-- Hero Header -->
    <header class="px-4 md:px-10 pt-16 pb-12 border-b border-[var(--silver)]/40 bg-gradient-to-b from-[var(--ivory-deep)] to-[var(--ivory)] relative">
        <div class="max-w-7xl mx-auto space-y-4">
            
            <nav class="text-[11px] font-semibold text-[var(--navy-light)] uppercase tracking-[0.08em] flex items-center gap-1.5">
                <a href="/cinema/<?php echo htmlspecialchars($supercategory); ?>" class="hover:text-navy transition-colors"><?php echo htmlspecialchars(ucwords($supercategory)); ?></a>
                <span>›</span>
                <a href="/cinema/<?php echo htmlspecialchars($supercategory); ?>/<?php echo htmlspecialchars($industry); ?>" class="hover:text-navy transition-colors"><?php echo htmlspecialchars(ucwords(str_replace('-', ' ', $industry))); ?></a>
            </nav>

            <h1 class="font-serif text-4xl md:text-5xl font-bold leading-tight">
                <?php echo htmlspecialchars($ceremony['name']); ?>
            </h1>
            
            <div class="flex items-center gap-3 text-xs text-[var(--navy-light)]">
                <span><?php echo $totalEditions; ?> EDITIONS (<?php echo $yearSpan; ?>)</span>
                <span>•</span>
                <span><?php echo htmlspecialchars($ceremony['country'] ?? 'Global'); ?></span>
            </div>
            
            <?php if (!empty($ceremony['description'])): ?>
                <p class="max-w-2xl text-[13px] leading-relaxed text-[var(--navy-light)] font-serif italic mt-2">
                    <?php echo htmlspecialchars($ceremony['description']); ?>
                </p>
            <?php endif; ?>
            
            <!-- Quick Stats -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 pt-6 border-t border-[var(--silver)]/40">
                
                <?php if ($records['most_decorated_film']): ?>
                <div class="card-royal p-4 cursor-pointer hover:border-[var(--gold)]/50 transition-colors" 
                     onclick="const url='/films/<?php echo htmlspecialchars($records['most_decorated_film']['film_slug']); ?>'; if(window.ajaxNavigate) { window.ajaxNavigate(url); } else { window.location.href=url; }">
                    <div class="text-[9px] font-bold text-[var(--navy-light)] uppercase tracking-wider mb-1">Most Decorated Film (Single Ed.)</div>
                    <div class="font-serif font-bold text-navy truncate">
                        <?php echo htmlspecialchars($records['most_decorated_film']['title']); ?>
                    </div>
                    <div class="text-[10px] text-[var(--gold)] font-bold">
                        <?php echo $records['most_decorated_film']['win_count']; ?> WINS (<?php echo $records['most_decorated_film']['year']; ?>)
                    </div>
                </div>
                <?php endif; ?>

                <?php if ($records['most_decorated_person']): ?>
                <div class="card-royal p-4 cursor-pointer hover:border-[var(--gold)]/50 transition-colors"
                     <?php if ($records['most_decorated_person']['slug']): ?>
                     onclick="const url='/<?php echo $records['most_decorated_person']['type'] === 'person' ? 'persons' : 'films'; ?>/<?php echo htmlspecialchars($records['most_decorated_person']['slug']); ?>'; if(window.ajaxNavigate) { window.ajaxNavigate(url); } else { window.location.href=url; }"
                     <?php endif; ?>
                     >
                    <div class="text-[9px] font-bold text-[var(--navy-light)] uppercase tracking-wider mb-1">Most Decorated Person</div>
                    <div class="font-serif font-bold text-navy truncate">
                        <?php echo htmlspecialchars($records['most_decorated_person']['name']); ?>
                    </div>
                    <div class="text-[10px] text-[var(--gold)] font-bold">
                        <?php echo $records['most_decorated_person']['win_count']; ?> TOTAL WINS
                    </div>
                </div>
                <?php endif; ?>

                <div class="card-royal p-4">
                    <div class="text-[9px] font-bold text-[var(--navy-light)] uppercase tracking-wider mb-1">Total Films Honoured</div>
                    <div class="font-serif font-bold text-navy truncate">
                        <?php echo number_format($records['total_films_honoured']); ?> FILMS
                    </div>
                    <div class="text-[10px] text-[var(--gold)] font-bold">IN DATABASE</div>
                </div>

                <?php if ($records['first_edition_winner']): ?>
                <div class="card-royal p-4">
                    <div class="text-[9px] font-bold text-[var(--navy-light)] uppercase tracking-wider mb-1">Inaugural Top Winner</div>
                    <div class="font-serif font-bold text-navy truncate">
                        <?php echo htmlspecialchars($records['first_edition_winner']['title']); ?>
                    </div>
                    <div class="text-[10px] text-[var(--gold)] font-bold">
                        <?php echo $records['first_edition_winner']['year']; ?>
                    </div>
                </div>
                <?php endif; ?>

          </div>

        </div>
    </header>

    <!-- Main timeline with decade filtering in Alpine.js -->
    <?php if ($totalEditions > 0): ?>
    <main class="max-w-7xl mx-auto" x-data="{
        activeDecade: 'All',
        searchQuery: '',
        hoveredYear: null,
        previewData: null,
        previewLoading: false,
        async hoverYear(year) {
            this.hoveredYear = year;
            this.previewLoading = true;
            this.previewData = null;
            try {
                const res = await fetch('/awardfilms-api/awards/preview.php?ceremony=<?php echo $slug; ?>&year=' + year);
                const data = await res.json();
                if (this.hoveredYear === year) { this.previewData = data; }
            } catch(e) { console.error(e); } finally {
                if (this.hoveredYear === year) this.previewLoading = false;
            }
        },
        leaveYear() { this.hoveredYear = null; this.previewData = null; }
    }">
        
        <!-- Decade Filter & Search row -->
        <div class="px-4 md:px-10 py-6 border-b border-[var(--silver)]/40 flex flex-col md:flex-row items-center justify-between gap-4 sticky top-[92px] bg-[rgba(250,247,242,0.95)] backdrop-blur-md z-40">
            <div class="flex flex-wrap gap-2">
                <button @click="activeDecade = 'All'" 
                        :class="activeDecade === 'All' ? 'bg-navy text-white' : 'bg-white border border-[var(--silver)] text-navy hover:bg-[var(--ivory-deep)]'" 
                        class="px-4 py-1.5 rounded-[2px] text-xs font-semibold uppercase tracking-[1px] transition-colors">
                    <?php echo __('All'); ?>
                </button>
                <?php foreach ($decadesSet as $dec): ?>
                <button @click="activeDecade = '<?php echo $dec; ?>'" 
                        :class="activeDecade === '<?php echo $dec; ?>' ? 'bg-navy text-white' : 'bg-white border border-[var(--silver)] text-navy hover:bg-[var(--ivory-deep)]'" 
                        class="px-4 py-1.5 rounded-[2px] text-xs font-semibold uppercase tracking-[1px] transition-colors">
                    <?php echo $dec; ?>
                </button>
                <?php endforeach; ?>
            </div>

            <!-- Search box within timeline -->
            <div class="w-full md:w-72 flex items-center border border-navy px-3 py-1.5 bg-white rounded-[2px] h-[36px]">
                <input type="text" placeholder="Search this archive..." 
                       x-model="searchQuery" 
                       class="w-full text-[12px] bg-transparent outline-none text-navy placeholder:opacity-50 font-sans">
            </div>
        </div>

        <!-- Timeline Grid -->
        <div class="px-4 md:px-10 py-8 relative">
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                
                <!-- Loop over decades in HTML/PHP -->
                <?php foreach ($decadesSet as $dec): ?>
                
                <!-- Decade Header shown only if current decade matches active filter -->
                <div class="col-span-full border-b border-[var(--silver)]/40 pb-2 pt-6 mb-2 text-[11px] font-bold uppercase tracking-[0.12em] text-[var(--navy-light)] first:pt-0"
                     x-show="activeDecade === 'All' || activeDecade === '<?php echo $dec; ?>'">
                    <?php echo $dec; ?>
                </div>

                <?php 
                foreach ($editions as $ed): 
                    $thisDecade = (floor($ed['year'] / 10) * 10) . 's';
                    if ($thisDecade !== $dec) continue;
                ?>
                <?php 
                    $searchPayload = [];
                    foreach ($ed['highlight_winners'] as $h) {
                        $searchPayload[] = strtolower($h['display_text'] . ' ' . $h['category_name']);
                    }
                ?>
                <div data-search="<?php echo htmlspecialchars(implode(' ', $searchPayload), ENT_QUOTES, 'UTF-8'); ?>"
                     x-show="(activeDecade === 'All' || activeDecade === '<?php echo $thisDecade; ?>') && (searchQuery === '' || '<?php echo $ed['year']; ?>'.includes(searchQuery) || $el.dataset.search.includes(searchQuery.toLowerCase()))"
                     class="card-royal p-5 text-start flex flex-col justify-between min-h-[180px] hover:bg-[var(--ivory-deep)] relative group"
                     @mouseenter="hoverYear(<?php echo $ed['year']; ?>)"
                     @mouseleave="leaveYear"
                     @click="window.ajaxNavigate('/<?php echo "$supercategory/$industry/" . $ceremony['slug'] . "/"; ?><?php echo $ed['year']; ?>')">

                    <!-- Latest badge -->
                    <?php if ($ed['year'] === $editions[0]['year']): ?>
                    <span class="absolute top-0 end-0 bg-[#D4A843] text-black text-[9px] font-bold uppercase px-2 py-0.5 rounded-bl-lg">
                        LATEST
                    </span>
                    <?php endif; ?>

                    <div>
                        <div class="font-serif text-[38px] font-bold leading-none text-navy group-hover:text-[var(--gold)] transition-colors">
                            <?php echo $ed['year']; ?>
                        </div>
                        <div class="text-[11px] font-semibold text-[var(--navy-light)] uppercase tracking-[0.8px] mt-1">
                            <?php echo $ed['edition_number'] ? $ed['edition_number'] . "th Edition" : "Annual Edition"; ?>
                        </div>
                    </div>

                    <!-- Highlight Winners -->
                    <div class="my-4 space-y-1.5 flex-1">
                        <?php foreach (array_slice($ed['highlight_winners'], 0, 3) as $h): ?>
                        <div class="text-[11px] text-[var(--navy-light)] truncate flex items-center gap-1.5">
                            <span class="shrink-0">🏆</span>
                            <?php
                            $catName = $h['category_name'];
                            if ($catName === strtoupper($catName)) {
                                $catName = ucwords(strtolower($catName));
                            }
                            ?>
                            <span class="font-bold text-navy"><?php echo htmlspecialchars(mb_strimwidth(__($catName), 0, 15, '...')); ?>:</span>
                            <span class="truncate"><?php echo htmlspecialchars($h['display_text']); ?></span>
                        </div>
                        <?php endforeach; ?>
                    </div>

                    <div class="text-[10px] text-[var(--navy-light)] font-bold uppercase tracking-wider flex justify-between items-center border-t border-[var(--silver)]/40 pt-3 mt-auto">
                        <span><?php echo $ed['total_categories']; ?> categories &middot; <?php echo $ed['total_winners']; ?> winners</span>
                        <span class="text-[var(--gold)] opacity-0 group-hover:opacity-100 transition-opacity duration-300">View Details &rarr;</span>
                    </div>

                </div>
                <?php endforeach; ?>
                <?php endforeach; ?>

            </div>

            <!-- Asynchronous Hover Preview Panel -->
            <div x-show="hoveredYear !== null" x-cloak
                 class="fixed md:absolute bg-[var(--ivory-card)] border border-[var(--silver)] rounded-[4px] p-5 shadow-2xl z-50 w-72 md:w-80 text-start top-1/4 right-6 pointer-events-none transition-all">
                <h4 class="font-serif text-lg font-bold text-navy mb-2" x-text="hoveredYear + ' Edition Preview'"></h4>
                <div x-show="previewLoading" class="flex items-center gap-2 py-6 text-xs text-[var(--navy-light)]">
                    <span class="animate-spin h-4 w-4 border-2 border-gold border-t-transparent rounded-full"></span> Loading Preview...
                </div>
                <div x-show="!previewLoading && previewData" class="space-y-4">
                    <div class="space-y-1 text-xs text-[var(--navy-light)]">
                        <div>ðŸ“ Venue: <span class="font-semibold text-navy" x-text="previewData?.venue || 'Not recorded'"></span></div>
                        <div>🎤 Host: <span class="font-semibold text-navy" x-text="previewData?.host || 'None'"></span></div>
                    </div>
                    <div class="border-t border-[var(--silver)]/40 pt-3">
                        <div class="text-[10px] font-bold text-[var(--navy-light)] uppercase tracking-wider mb-2">Top Category Winners</div>
                        <div class="space-y-2">
                            <template x-for="w in previewData?.top_winners">
                                <div class="text-[11px] leading-snug">
                                    <div class="font-bold text-[var(--gold)]" x-text="w.category_name"></div>
                                    <div class="text-navy" x-text="w.winner_text"></div>
                                </div>
                            </template>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </main>
    <?php else: ?>
    <main class="max-w-7xl mx-auto px-4 md:px-10 py-16 text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[var(--ivory-deep)] text-[var(--gold)] text-2xl mb-4">
            🏆
        </div>
        <h3 class="font-serif text-2xl font-bold text-navy mb-2"><?php echo __('No Records Available Yet'); ?></h3>
        <p class="text-[var(--navy-light)] font-sans text-sm max-w-md mx-auto">
            <?php echo __('We are currently importing and verifying the awards archive for this ceremony. Please check back soon.'); ?>
        </p>
    </main>
    <?php endif; ?>

</div>

<?php
require_once __DIR__ . '/layouts/footer.php';
?>

