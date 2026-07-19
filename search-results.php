<?php
require_once __DIR__ . '/lib/queries.php';
require_once __DIR__ . '/lib/navigation.php';
require_once __DIR__ . '/lib/searchEngine.php';

$query = $_GET['q'] ?? '';
$type = $_GET['type'] ?? 'all';
$page = isset($_GET['page']) ? (int)$_GET['page'] : 1;

$currentPage = max(1, $page);
$limit = ($type === 'all') ? 50 : 24;
$offset = ($currentPage - 1) * $limit;

$results = ['films' => [], 'persons' => [], 'ceremonies' => []];
if (strlen($query) >= 2) {
    $results = SearchEngine::search($query, $limit, $offset);
}

$hasResults = count($results['films']) > 0 || count($results['persons']) > 0 || count($results['ceremonies']) > 0;

// â”€â”€â”€ CHECK 1: CEREMONY EDITION MATCH (e.g. "Filmfare 2022") â”€â”€â”€
$matchedEdition = null;
preg_match('/\b(19\d{2}|20[0-2]\d)\b/', $query, $yearMatch);
if ($yearMatch && strlen($query) >= 4) {
    $year = (int)$yearMatch[0];
    $ceremonySlug = "";
    $queryLower = strtolower($query);

    if (strpos($queryLower, 'filmfare') !== false) {
        $ceremonySlug = (strpos($queryLower, 'south') !== false) ? 'filmfare-awards-south' : 'filmfare-awards';
    } elseif (strpos($queryLower, 'iifa') !== false) {
        $ceremonySlug = 'iifa-awards';
    } elseif (strpos($queryLower, 'oscar') !== false || strpos($queryLower, 'academy') !== false) {
        $ceremonySlug = 'oscars';
    } elseif (strpos($queryLower, 'bafta') !== false) {
        $ceremonySlug = 'bafta';
    } elseif (strpos($queryLower, 'cannes') !== false) {
        $ceremonySlug = 'cannes';
    } elseif (strpos($queryLower, 'lux') !== false) {
        $ceremonySlug = 'lux-style-awards';
    } elseif (count($results['ceremonies']) > 0) {
        $ceremonySlug = $results['ceremonies'][0]['slug'];
    }

    if ($ceremonySlug) {
        $matchedEdition = getEditionWithAllCategories($ceremonySlug, $year);
    }
}

// Helper function to find dynamic paths
function getCeremonyPath($cSlug) {
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

function getEditionPath($cSlug, $eSlug) {
    global $NAV_DATA;
    $year = $eSlug;
    if (preg_match('/-(\d{4})$/', $eSlug, $matches)) {
        $year = $matches[1];
    }
    foreach ($NAV_DATA as $cat) {
        foreach ($cat['industries'] as $ind) {
            foreach ($ind['ceremonies'] as $c) {
                if ($c['slug'] === $cSlug) {
                    return "/" . $cat['slug'] . "/" . $ind['slug'] . "/" . $c['slug'] . "/" . $year;
                }
            }
        }
    }
    return "/search?q=" . urlencode($eSlug);
}

$pageTitle = "Search Results for \"" . htmlspecialchars($query) . "\"";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';
?>

<div class="min-h-screen bg-[#FAFAF8] py-12 px-6 text-start">
    <div class="mx-auto max-w-5xl">
        <!-- Breadcrumbs -->
        <nav class="mb-6 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--navy-light)]">
            <a href="/" class="hover:text-[var(--gold)]">Home</a>
            <span>/</span>
            <span class="text-navy font-bold">Search</span>
        </nav>

        <!-- Heading -->
        <header class="mb-10 border-b border-[var(--silver)]/40 pb-6">
            <h1 class="font-serif text-3xl md:text-4xl font-bold text-navy">
                <?php echo $query ? 'Search results for "' . htmlspecialchars($query) . '"' : 'Search AwardFilms'; ?>
            </h1>
            <?php if ($query && $hasResults): ?>
                <p class="text-xs text-[var(--navy-light)] mt-1 font-bold">
                    Faceted database search found <?php echo count($results['films']); ?> items
                </p>
            <?php endif; ?>
        </header>

        <!-- INTENT MESSAGE (AI-LIKE RESPONSE) -->
        <?php if (!empty($results['intent_message'])): ?>
            <div class="mb-8 p-4 bg-blue-50 border-l-4 border-blue-500 text-blue-900 rounded shadow-sm flex items-start gap-3">
                <svg class="w-6 h-6 shrink-0 mt-0.5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                <div>
                    <h3 class="font-bold text-sm mb-1">AI Assistant</h3>
                    <p class="text-sm"><?php echo htmlspecialchars($results['intent_message']); ?></p>
                </div>
            </div>
        <?php endif; ?>

        <!-- ——— CASE A: CEREMONY EDITION MATCH ——— -->
        <?php if ($matchedEdition): ?>
            <!-- Detail view for ceremony edition -->
            <div class="space-y-8 animate-fade-in text-start">
                <div class="rounded-xl border border-[var(--silver)]/60 bg-white p-6 shadow-sm">
                    <span class="text-xs font-bold uppercase tracking-wider text-[var(--gold)]">Ceremony Edition Page</span>
                    <h2 class="font-serif text-2xl font-black text-navy mt-1">
                        <?php echo htmlspecialchars($matchedEdition['ceremony']['name'] . ' (' . $matchedEdition['edition']['year'] . ')'); ?>
                    </h2>
                    <div class="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs text-[var(--navy-light)] font-bold">
                        <?php if ($matchedEdition['edition']['venue']): ?><span>📍 <?php echo htmlspecialchars($matchedEdition['edition']['venue']); ?></span><?php endif; ?>
                        <?php if ($matchedEdition['edition']['host']): ?><span>🎤 Host: <?php echo htmlspecialchars($matchedEdition['edition']['host']); ?></span><?php endif; ?>
                    </div>
                </div>

                <div class="space-y-6">
                    <h3 class="font-serif text-lg font-bold text-navy">Category Winners &amp; Nominees</h3>
                    <div class="grid gap-6 md:grid-cols-2">
                        <?php foreach ($matchedEdition['categories'] as $c): ?>
                        <div class="bg-white border border-[var(--silver)] rounded-lg p-5 shadow-sm">
                            <div class="flex justify-between items-center gap-3 border-b border-[var(--silver)]/30 pb-3 mb-3">
                                <span class="font-bold text-navy text-sm"><?php echo htmlspecialchars($c['name']); ?></span>
                                <span class="text-[10px] text-[var(--navy-light)] bg-navy/5 border border-[var(--silver)] px-2 py-0.5 rounded-[2px]"><?php echo htmlspecialchars($c['department']); ?></span>
                            </div>
                            <div class="space-y-2">
                                <?php foreach ($c['nominations'] as $n): ?>
                                <div class="flex justify-between items-center text-xs gap-3">
                                    <div class="flex items-center gap-2">
                                        <span class="text-xs"><?php echo $n['is_winner'] ? '🏆' : '○'; ?></span>
                                        <span class="font-semibold <?php echo $n['is_winner'] ? 'text-navy' : 'text-[var(--navy-light)]'; ?>">
                                            <?php echo htmlspecialchars($n['person']['name'] ?? $n['nominee_text']); ?>
                                        </span>
                                        <?php if ($n['film']): ?>
                                            <span class="text-gray-400">&mdash; <?php echo htmlspecialchars($n['film']['title']); ?></span>
                                        <?php endif; ?>
                                    </div>
                                    <?php 
                                    $destUrl = $n['film'] ? '/films/' . $n['film']['slug'] : ($n['person'] ? '/persons/' . $n['person']['slug'] : null);
                                    if ($destUrl):
                                    ?>
                                        <a href="<?php echo $destUrl; ?>" class="text-[var(--navy-light)] font-bold hover:text-[var(--gold)]">&rarr;</a>
                                    <?php endif; ?>
                                </div>
                                <?php endforeach; ?>
                            </div>
                        </div>
                        <?php endforeach; ?>
                    </div>
                </div>
            </div>

        <!-- ——— CASE B: STANDARD RESULTS GRID ——— -->
        <?php else: ?>
            <div class="space-y-10">
                <?php if (!$hasResults && strlen($query) >= 2): ?>
                <div class="rounded-lg border border-[var(--silver)] bg-white p-12 text-center shadow-sm">
                    <p class="text-sm font-bold text-navy mb-4">No results found for "<?php echo htmlspecialchars($query); ?>".</p>
                    <p class="text-xs text-[var(--navy-light)] max-w-md mx-auto leading-relaxed">
                        We couldn't find any awards, films, or people matching your search.<br>
                        Try a name, film, ceremony, or year — e.g. 'Filmfare Best Actor 2020' or 'Shah Rukh Khan'.
                    </p>
                </div>
                <?php endif; ?>

                <?php if ($hasResults): ?>
                <div class="space-y-6">
                    <h2 class="mb-6 flex items-center gap-2 font-serif text-xl font-bold text-navy">🎬 Awards &amp; Nominations</h2>
                    <?php if (count($results['films']) > 0): ?>
                        <div class="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
                            <?php foreach ($results['films'] as $film): ?>
                            <div class="card-royal p-3 flex gap-4 items-center h-28 block relative">
                                <a href="<?php echo htmlspecialchars(getEditionPath($film['ceremony_slug'], $film['edition_slug'])); ?>" 
                                   class="relative h-20 w-14 shrink-0 bg-navy rounded overflow-hidden border border-[var(--silver)] hover:opacity-90 block">
                                    <img src="/img-proxy.php?film=<?php echo $film['id']; ?>" alt="" class="w-full h-full object-cover">
                                </a>
                                <div class="min-w-0 flex-1">
                                    <a href="<?php echo htmlspecialchars(getEditionPath($film['ceremony_slug'], $film['edition_slug'])); ?>" 
                                       class="font-bold text-xs text-navy leading-snug hover:text-[var(--gold)] transition-colors line-clamp-2"
                                       title="<?php echo htmlspecialchars(($film['category_name'] ?? 'Nomination') . ' — ' . ($film['ceremony_name'] ?? 'Award') . ' ' . ($film['edition_year'] ?? $film['year'])); ?>">
                                        <?php echo htmlspecialchars(($film['category_name'] ?? 'Nomination') . ' — ' . ($film['ceremony_name'] ?? 'Award') . ' ' . ($film['edition_year'] ?? $film['year'])); ?>
                                    </a>
                                    <p class="text-[11px] text-[var(--navy-light)] mt-1 truncate">
                                        <?php if (!empty($film['nominee_url']) && $film['nominee_url'] !== '#'): ?>
                                            <a href="<?php echo htmlspecialchars($film['nominee_url']); ?>" class="hover:text-[var(--gold)] hover:underline font-medium">
                                                <?php echo htmlspecialchars($film['title']); ?>
                                            </a>
                                        <?php else: ?>
                                            <span class="font-medium"><?php echo htmlspecialchars($film['title']); ?></span>
                                        <?php endif; ?>
                                    </p>
                                </div>
                            </div>
                            <?php endforeach; ?>
                        </div>
                    <?php else: ?>
                        <p class="text-xs text-gray-400 italic">No matching awards.</p>
                    <?php endif; ?>
                </div>
                <?php endif; ?>

                <!-- Pagination navigation links -->
                <?php if (strlen($query) >= 2 && $hasResults): ?>
                <div class="mt-12 flex justify-center gap-4">
                    <?php if ($currentPage > 1): ?>
                        <a href="/search?q=<?php echo urlencode($query); ?>&page=<?php echo $currentPage - 1; ?>" class="px-4 py-2 border border-[var(--silver)] bg-white text-xs font-bold uppercase rounded-[2px] hover:bg-gray-50 transition-colors">&larr; Previous</a>
                    <?php endif; ?>
                    <?php if (count($results['films']) === $limit): ?>
                        <a href="/search?q=<?php echo urlencode($query); ?>&page=<?php echo $currentPage + 1; ?>" class="px-4 py-2 border border-[var(--silver)] bg-white text-xs font-bold uppercase rounded-[2px] hover:bg-gray-50 transition-colors">Next &rarr;</a>
                    <?php endif; ?>
                </div>
                <?php endif; ?>

            </div>
        <?php endif; ?>

    </div>
</div>

<?php 
require_once __DIR__ . '/layouts/footer.php'; 
?>

