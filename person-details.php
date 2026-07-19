<?php
require_once __DIR__ . '/lib/queries.php';
require_once __DIR__ . '/lib/navigation.php';

$slug = $_GET['slug'] ?? '';
$data = getPersonWithNominations($slug);

// Fallback: many famous people are aliased in the 'films' table in this dataset
if (!$data) {
    $data = getFilmWithNominations($slug);
    if ($data && isset($data['film'])) {
        $data['person'] = $data['film'];
        $data['person']['name'] = $data['film']['title'];
    } else {
        $data = null; // Ensure null if fallback also fails
    }
}

if (!$data) {
    http_response_code(404);
    $pageTitle = "Profile Not Found";
    require_once __DIR__ . '/layouts/head.php';
    require_once __DIR__ . '/layouts/header.php';
    echo '<div class="min-h-screen bg-[var(--ivory)] text-navy pt-32 pb-12 px-6 flex flex-col items-center justify-center animate-fade-in">';
    echo '<h1 class="font-serif text-[32px] md:text-[40px] text-navy mb-4">' . __('Profile Not Found') . '</h1>';
    echo '<p class="text-[var(--silver)] font-sans text-[15px] tracking-wide mb-8">' . __('No records found for this profile yet.') . '</p>';
    echo '<a href="/" class="inline-block px-8 py-3 bg-navy text-[var(--ivory)] rounded hover:bg-[var(--gold)] transition-colors uppercase tracking-[2px] text-[12px] font-bold">' . __('Return Home') . '</a>';
    echo '</div>';
    require_once __DIR__ . '/layouts/footer.php';
    exit;
}

$person = $data['person'];
$nominations = $data['nominations'];
$wins = $data['wins'];
$nominationCount = $data['nominationCount'];

// Group nominations by ceremony
$byCeremony = [];
foreach ($nominations as $n) {
    $cSlug = $n['ceremonySlug'];
    if (!isset($byCeremony[$cSlug])) {
        $byCeremony[$cSlug] = [
            'name' => $n['ceremonyName'],
            'wins' => 0,
            'noms' => 0
        ];
    }
    $byCeremony[$cSlug]['noms']++;
    if ($n['isWinner']) {
        $byCeremony[$cSlug]['wins']++;
    }
}

// Helper function to build timeline grouping by Year -> Film
$byYear = [];
foreach ($nominations as $n) {
    $year = $n['year'] ?: 0;
    $filmKey = $n['filmSlug'] ?: '__none__';

    if (!isset($byYear[$year])) {
        $byYear[$year] = [];
    }

    if (!isset($byYear[$year][$filmKey])) {
        $byYear[$year][$filmKey] = [
            'filmTitle' => $n['filmTitle'] ?: null,
            'filmSlug' => $n['filmSlug'] ?: null,
            'nominations' => []
        ];
    }
    $byYear[$year][$filmKey]['nominations'][] = $n;
}
krsort($byYear);

// Helper function to retrieve regional link
function getCeremonyPathLink($cSlug) {
    global $NAV_DATA;
    foreach ($NAV_DATA as $cat) {
        foreach ($cat['industries'] as $ind) {
            foreach ($ind['ceremonies'] as $c) {
                if ($c['slug'] === $cSlug) {
                    return "/" . $cat['slug'] . "/" . $ind['slug'] . "/" . $c['slug'];
                }
            }
        }
    }
    return "/search?q=" . urlencode($cSlug);
}

$pageTitle = $person['name'] . " â€” Career Awards & Nominations";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';
?>

<div class="mx-auto max-w-7xl px-6 py-12 text-start">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-8 flex items-center gap-2 text-sm text-[var(--navy-light)] font-medium">
        <a href="/" class="hover:text-[#C9A84C] transition-colors">Home</a>
        <span>/</span>
        <a href="/persons" class="hover:text-[#C9A84C] transition-colors">People</a>
        <span>/</span>
        <span class="line-clamp-1 text-navy font-bold"><?php echo htmlspecialchars($person['name']); ?></span>
    </nav>

    <!-- Profile Grid Layout -->
    <div class="grid gap-10 lg:grid-cols-[260px_1fr]">
        
        <!-- Left Sidebar: photo + details + ceremony tallies -->
        <aside class="space-y-6">
            <!-- Photo avatar -->
            <div class="relative mx-auto aspect-square w-52 overflow-hidden rounded-2xl border border-[#C9A84C]/25 bg-white shadow-lg lg:mx-0 lg:w-full">
                <img src="/img-proxy.php?<?php echo isset($data['film']) ? 'film=' . htmlspecialchars($person['id']) : 'person=' . htmlspecialchars($person['id']); ?>" alt="<?php echo htmlspecialchars($person['name']); ?>" class="w-full h-full object-cover object-top">
            </div>

            <!-- Meta attributes -->
            <div class="space-y-2 rounded-xl border border-[var(--silver)] bg-white p-5 text-sm text-[var(--navy-light)] font-medium shadow-sm">
                <?php if (isset($person['birth_year']) && $person['birth_year']): ?>
                    <div class="flex items-center justify-between">
                        <span>Born</span>
                        <span class="font-bold text-navy"><?php echo $person['birth_year']; ?></span>
                    </div>
                <?php endif; ?>
                <?php if ($person['nationality']): ?>
                    <div class="flex items-center justify-between">
                        <span>Nationality</span>
                        <span class="font-bold text-navy"><?php echo htmlspecialchars($person['nationality']); ?></span>
                    </div>
                <?php endif; ?>
                <div class="flex items-center justify-between">
                    <span>Total Wins</span>
                    <span class="font-bold text-[var(--gold)]">ðŸ† <?php echo $wins; ?></span>
                </div>
                <div class="flex items-center justify-between">
                    <span>Nominations</span>
                    <span class="font-bold text-navy"><?php echo $nominationCount; ?></span>
                </div>
                <?php if (isset($person['imdb_id']) && $person['imdb_id']): ?>
                    <a href="https://www.imdb.com/name/<?php echo $person['imdb_id']; ?>" target="_blank" rel="noopener noreferrer"
                       class="mt-2 block rounded-lg border border-[var(--silver)] p-2 text-center text-xs text-[var(--gold)] font-bold transition-all hover:border-[var(--gold)] hover:bg-gray-50">
                        View on IMDb â†—
                    </a>
                <?php endif; ?>
            </div>

            <!-- Tallies grouped by Ceremony -->
            <?php if (count($byCeremony) > 0): ?>
            <div class="space-y-2.5">
                <h2 class="text-xs font-bold uppercase tracking-widest text-[var(--navy-light)]">By Ceremony</h2>
                <?php 
                uasort($byCeremony, fn($a, $b) => $b['wins'] - $a['wins']);
                foreach ($byCeremony as $cSlug => $c):
                    $winRatio = $c['noms'] > 0 ? ($c['wins'] / $c['noms']) * 100 : 0;
                ?>
                <div class="rounded-lg border border-[var(--silver)] bg-white p-4 shadow-sm space-y-3">
                    <p class="text-xs font-bold uppercase tracking-wider text-[var(--gold)]"><?php echo htmlspecialchars($c['name']); ?></p>
                    <div class="flex justify-between text-xs text-[var(--navy-light)] font-bold">
                        <span>ðŸ† <?php echo $c['wins']; ?> Win<?php echo $c['wins'] !== 1 ? 's' : ''; ?></span>
                        <span><?php echo $c['noms']; ?> Nom<?php echo $c['noms'] !== 1 ? 's' : ''; ?></span>
                    </div>
                    <div class="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                        <div class="h-full bg-[var(--gold)]" style="width: <?php echo $winRatio; ?>%"></div>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>
            <?php endif; ?>
        </aside>

        <!-- Right Side: Career stats and timeline history -->
        <div class="space-y-8">
            <div>
                <?php if ($wins > 0): ?>
                <p class="mb-2 text-xs font-bold uppercase tracking-[0.2em] text-[var(--gold)]">
                    ðŸ† <?php echo $wins; ?> Award<?php echo $wins !== 1 ? "s" : ""; ?> Won Across <?php echo count($byCeremony); ?> Ceremon<?php echo count($byCeremony) !== 1 ? "ies" : "y"; ?>
                </p>
                <?php endif; ?>
                <h1 class="text-4xl font-serif font-black text-navy sm:text-5xl"><?php echo htmlspecialchars($person['name']); ?></h1>
            </div>

            <!-- Overall Acclaim bar -->
            <?php 
            $overallRatio = $nominationCount > 0 ? ($wins / $nominationCount) * 100 : 0;
            ?>
            <div class="rounded-xl border border-[var(--gold)]/20 bg-gradient-to-br from-navy to-[#2E3F5C] p-5 text-white">
                <p class="text-xs font-bold uppercase tracking-wider text-[var(--gold-light)] mb-3">All Ceremonies Combined</p>
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div class="flex flex-col">
                        <span class="text-4xl font-black text-[var(--gold-light)]"><?php echo $wins; ?></span>
                        <span class="text-[10px] uppercase font-bold tracking-wider opacity-60 mt-1">Wins</span>
                    </div>
                    <div class="flex flex-col">
                        <span class="text-4xl font-black text-white"><?php echo $nominationCount; ?></span>
                        <span class="text-[10px] uppercase font-bold tracking-wider opacity-60 mt-1">Nominations</span>
                    </div>
                </div>
                <div class="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                    <div class="h-full bg-[var(--gold)]" style="width: <?php echo $overallRatio; ?>%"></div>
                </div>
                <div class="flex justify-between text-[11px] opacity-75 mt-2">
                    <span>Acclaim Ratio</span>
                    <span><?php echo round($overallRatio); ?>%</span>
                </div>
            </div>

            <!-- Career Biography -->
            <?php if (isset($person['biography']) && $person['biography']): ?>
            <div>
                <h2 class="mb-2 text-xs font-bold uppercase tracking-widest text-[var(--navy-light)]">Biography</h2>
                <p class="leading-relaxed text-[var(--navy-light)] text-sm"><?php echo htmlspecialchars($person['biography']); ?></p>
            </div>
            <?php endif; ?>

            <!-- Timeline -->
            <?php if (count($byYear) > 0): ?>
            <div class="space-y-6">
                <h2 class="text-xl font-serif font-bold text-navy">Career Awards Timeline <span class="text-xs text-[var(--navy-light)] font-normal font-sans">(<?php echo $nominationCount; ?> nominations)</span></h2>
                
                <div class="relative space-y-8 before:absolute before:left-[19px] before:top-2 before:h-[calc(100%-16px)] before:w-px before:bg-navy/10 ps-12 text-start">
                    <?php foreach ($byYear as $year => $filmsGroup): ?>
                    <div class="relative">
                        <!-- Year marker -->
                        <div class="absolute -left-[52px] top-1 flex h-10 w-10 items-center justify-center rounded-full border border-[var(--gold)]/30 bg-[var(--ivory)] text-xs font-bold text-[var(--gold)]">
                            <?php echo $year ?: "?"; ?>
                        </div>

                        <div class="space-y-4">
                            <?php foreach ($filmsGroup as $filmKey => $fGroup): ?>
                            <div class="rounded-lg border border-[var(--silver)] bg-white overflow-hidden shadow-sm">
                                <?php if ($fGroup['filmTitle']): ?>
                                <div class="bg-gray-50 border-b border-[var(--silver)]/40 px-4 py-2.5 flex items-center gap-2">
                                    <span class="text-xs">🎬</span>
                                    <?php if ($fGroup['filmSlug']): ?>
                                        <a href="/films/<?php echo $fGroup['filmSlug']; ?>" class="text-sm font-bold text-navy hover:text-[var(--gold)] transition-colors">
                                            <?php echo htmlspecialchars($fGroup['filmTitle']); ?>
                                        </a>
                                    <?php else: ?>
                                        <span class="text-sm font-bold text-navy"><?php echo htmlspecialchars($fGroup['filmTitle']); ?></span>
                                    <?php endif; ?>
                                </div>
                                <?php endif; ?>

                                <!-- Nominations table/list in this film -->
                                <div class="divide-y divide-gray-100">
                                    <?php foreach ($fGroup['nominations'] as $nom): ?>
                                    <div class="flex items-center justify-between gap-3 px-4 py-3 <?php echo $nom['isWinner'] ? 'bg-[var(--gold)]/5' : ''; ?>">
                                        <div class="flex items-center gap-3">
                                            <span class="text-xs leading-none shrink-0"><?php echo $nom['isWinner'] ? 'ðŸ†' : '○'; ?></span>
                                            <span class="text-xs font-bold text-navy"><?php echo htmlspecialchars($nom['categoryName']); ?></span>
                                        </div>
                                        <div class="flex items-center gap-2">
                                            <a href="<?php echo getCeremonyPathLink($nom['ceremonySlug']); ?>" 
                                               class="shrink-0 rounded-full border border-[var(--silver)] px-3 py-1 text-[10px] font-bold text-[var(--navy-light)] hover:border-[var(--gold)]/40 hover:text-[var(--gold)] transition-colors whitespace-nowrap bg-white">
                                                <?php echo htmlspecialchars($nom['ceremonyName']); ?>
                                            </a>
                                            <?php if ($nom['isWinner']): ?>
                                                <span class="shrink-0 bg-[var(--gold)] text-white text-[9px] font-bold uppercase px-1.5 py-0.5 rounded">WON</span>
                                            <?php endif; ?>
                                        </div>
                                    </div>
                                    <?php endforeach; ?>
                                </div>
                            </div>
                            <?php endforeach; ?>
                        </div>
                    </div>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php endif; ?>

        </div>
    </div>
</div>

<?php 
require_once __DIR__ . '/layouts/footer.php'; 
?>

