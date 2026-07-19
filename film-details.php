<?php
require_once __DIR__ . '/lib/queries.php';

$slug = $_GET['slug'] ?? '';
$data = getFilmWithNominations($slug);

if (!$data) {
    http_response_code(404);
    $pageTitle = "Film Not Found";
    require_once __DIR__ . '/layouts/head.php';
    require_once __DIR__ . '/layouts/header.php';
    echo '<div class="min-h-screen bg-[var(--ivory)] text-navy pt-32 pb-12 px-6 flex flex-col items-center justify-center animate-fade-in">';
    echo '<h1 class="font-serif text-[32px] md:text-[40px] text-navy mb-4">' . __('Film Not Found') . '</h1>';
    echo '<p class="text-[var(--silver)] font-sans text-[15px] tracking-wide mb-8">' . __('No records found for this film yet.') . '</p>';
    echo '<a href="/films" class="inline-block px-8 py-3 bg-navy text-[var(--ivory)] rounded hover:bg-[var(--gold)] transition-colors uppercase tracking-[2px] text-[12px] font-bold">' . __('Browse Database') . '</a>';
    echo '</div>';
    require_once __DIR__ . '/layouts/footer.php';
    exit;
}

$film = $data['film'];
$nominations = $data['nominations'];
$wins = $data['wins'];
$nominationCount = $data['nominationCount'];

// Fetch streaming links & similar films (same country)
$streamingLinks = getStreamingLinks($film['id']);
$similarFilmsRaw = getFilmsByCountry($film['country'] ?: 'India', 5, 0);

// Filter out current film
$similarFilms = [];
foreach ($similarFilmsRaw as $f) {
    if ($f['filmSlug'] !== $slug) {
        $similarFilms[] = $f;
    }
}
$similarFilms = array_slice($similarFilms, 0, 3);

// Group nominations by edition
$byEdition = [];
foreach ($nominations as $n) {
    $editionKey = $n['ceremonySlug'] . '_' . $n['year'];
    if (!isset($byEdition[$editionKey])) {
        $byEdition[$editionKey] = [
            'name' => $n['ceremonyName'],
            'year' => $n['year'],
            'wins' => 0,
            'noms' => []
        ];
    }
    $byEdition[$editionKey]['noms'][] = $n;
    if ($n['isWinner']) {
        $byEdition[$editionKey]['wins']++;
    }
}

// Find director name
$directorName = null;
foreach ($nominations as $n) {
    if (strpos(strtolower($n['categoryName']), 'director') !== false && $n['isWinner']) {
        $directorName = $n['nomineeText'];
        break;
    }
}

$genres = array_filter(array_map('trim', explode(',', $film['genre'] ?: '')));

$pageTitle = $film['title'] . " (" . ($film['year'] ?: '—') . ") — Awards & Nominations";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';

// Donut chart calculations
$totalNoms = $nominationCount;
$totalWins = $wins;
$winPercent = $totalNoms > 0 ? round(($totalWins / $totalNoms) * 100) : 0;
$radius = 30;
$circumference = 2 * M_PI * $radius;
$strokeDashoffset = $totalNoms > 0 ? $circumference - ($totalWins / $totalNoms) * $circumference : $circumference;
?>

<div class="min-h-screen bg-[#FAF7F2] text-navy animate-fade-in pb-12" x-data="{
    resolvedYoutubeId: <?php echo json_encode($film['trailer_youtube_id'] ?? null); ?>,
    loadingTrailer: false,
    watchlist: JSON.parse(localStorage.getItem('user_watchlist') || '[]'),
    inWatchlist(id) {
        return this.watchlist.some(f => f.id === id);
    },
    toggleWatchlist(id, title, poster, year) {
        if (this.inWatchlist(id)) {
            this.watchlist = this.watchlist.filter(f => f.id !== id);
        } else {
            this.watchlist.push({ id: id, title: title, poster_url: poster, year: year });
        }
        localStorage.setItem('user_watchlist', JSON.stringify(this.watchlist));
    },
    async init() {
        if (this.resolvedYoutubeId) return;
        this.loadingTrailer = true;
        const cacheKey = 'yt-trailer-' + <?php echo json_encode(strtolower(preg_replace('/[^a-z0-9]+/i', '-', $film['title']))); ?>;
        const cached = localStorage.getItem(cacheKey);
        if (cached) {
            try {
                const parsed = JSON.parse(cached);
                if (parsed.videoId) {
                    this.resolvedYoutubeId = parsed.videoId;
                    this.loadingTrailer = false;
                    return;
                }
            } catch (e) {
                localStorage.removeItem(cacheKey);
            }
        }
        try {
            const res = await fetch('/awardfilms-api/youtube.php?title=' + encodeURIComponent(<?php echo json_encode($film['title']); ?>) + '&year=' + <?php echo json_encode($film['year'] ?: ''); ?>);
            const data = await res.json();
            if (data.videoId) {
                localStorage.setItem(cacheKey, JSON.stringify({ videoId: data.videoId }));
                this.resolvedYoutubeId = data.videoId;
            }
        } catch(e) {
            console.error('Failed to load trailer', e);
        } finally {
            this.loadingTrailer = false;
        }
    }
}">

    <!-- Dynamic TMDb poster caching and proxy logic is now handled by img-proxy.php -->
    <?php
    // We intentionally removed the inline TMDB fetch code here.
    ?>

    <!-- COMPACT FILM HEADER (Ivory / Gold Theme with tight spacing) -->
    <section class="relative bg-[#F2EDE4] border-b border-[var(--silver)]/40 py-6">
        <div class="mx-auto max-w-7xl px-6 w-full grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
            
            <!-- Compact Movie Poster (max 180px width for better tight spacing balance) -->
            <div class="md:col-span-2 flex justify-center md:justify-start">
                <div class="relative aspect-[2/3] w-36 md:w-full rounded-[3px] overflow-hidden border border-[var(--gold)]/30 shadow-[0_8px_20px_var(--shadow)] bg-white transition-transform duration-300 hover:scale-[1.02]">
                    <img src="/img-proxy.php?film=<?php echo $film['id']; ?>" alt="<?php echo htmlspecialchars($film['title']); ?>" class="w-full h-full object-cover">
                </div>
            </div>

            <!-- Details -->
            <div class="md:col-span-10 space-y-3 text-center md:text-start">
                <nav class="text-[9px] font-bold text-[var(--gold)] uppercase tracking-[3px] flex justify-center md:justify-start items-center gap-1">
                    <a href="/" class="hover:text-[var(--gold-light)] transition-colors">Home</a>
                    <span>/</span>
                    <a href="/films" class="hover:text-[var(--gold-light)] transition-colors">Films</a>
                    <span>/</span>
                    <span class="text-navy opacity-80"><?php echo htmlspecialchars($film['title']); ?></span>
                </nav>

                <h1 class="font-serif text-3xl md:text-4xl font-bold text-navy tracking-tight leading-tight">
                    <?php echo htmlspecialchars($film['title']); ?>
                </h1>
                
                <div class="space-y-2">
                    <div class="flex flex-wrap justify-center md:justify-start items-center gap-2 text-xs font-semibold text-[var(--navy-light)]">
                        <?php if ($film['year']): ?>
                            <span class="bg-navy/10 px-2.5 py-0.5 rounded text-xs text-navy font-bold"><?php echo $film['year']; ?></span>
                        <?php endif; ?>
                        <?php if ($film['country']): ?>
                            <span>• <?php echo htmlspecialchars($film['country']); ?></span>
                        <?php endif; ?>
                        <?php if (isset($film['runtime']) && $film['runtime']): ?>
                            <span>• <?php echo $film['runtime']; ?> min</span>
                        <?php endif; ?>
                    </div>
                    
                    <?php if ($directorName): ?>
                        <p class="text-xs text-[var(--navy-light)]">
                            Director: <span class="text-navy font-bold"><?php echo htmlspecialchars($directorName); ?></span>
                        </p>
                    <?php endif; ?>

                    <?php if ($genres): ?>
                        <div class="flex flex-wrap gap-1.5 justify-center md:justify-start pt-0.5">
                            <?php foreach ($genres as $g): ?>
                                <span class="border border-[var(--gold)]/30 text-[var(--gold)] px-2.5 py-0.5 rounded-full text-[10px] font-semibold tracking-wide bg-[var(--gold-pale)]/10">
                                    <?php echo htmlspecialchars($g); ?>
                                </span>
                            <?php endforeach; ?>
                        </div>
                    <?php endif; ?>
                </div>

                <div class="flex flex-wrap justify-center md:justify-start gap-2 pt-1">
                    <span class="bg-[var(--gold)] text-white text-[10px] font-bold uppercase tracking-wider px-3.5 py-1.5 rounded-[2px]">
                        🏆 <?php echo $wins; ?> Wins
                    </span>
                    <span class="bg-white text-navy border border-[var(--silver)] text-[10px] font-bold uppercase tracking-wider px-3.5 py-1.5 rounded-[2px]">
                        🎯 <?php echo $nominationCount; ?> Nominations
                    </span>
                    <button @click="toggleWatchlist(<?php echo $film['id']; ?>, <?php echo json_encode($film['title']); ?>, <?php echo json_encode($film['poster_url']); ?>, <?php echo $film['year'] ?: 0; ?>)"
                            class="flex items-center gap-1.5 border text-[10px] font-bold uppercase tracking-wider px-3.5 py-1.5 rounded-[2px] cursor-pointer transition-all duration-300 shadow-sm outline-none"
                            :class="inWatchlist(<?php echo $film['id']; ?>) ? 'bg-[#6B1C2A] text-white border-transparent hover:bg-[#8B2635]' : 'bg-white text-navy border-[var(--silver)] hover:bg-gray-50'">
                        <span x-text="inWatchlist(<?php echo $film['id']; ?>) ? '❤️ Bookmarked' : '🤍 Add Watchlist'"></span>
                    </button>
                </div>
            </div>
        </div>
    </section>

    <!-- MAIN BODY SECTION WITH TIGHT spacing -->
    <main class="mx-auto max-w-7xl px-6 py-6">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            
            <!-- LEFT COLUMN: AWARDS & TRAILER (65% width) -->
            <div class="lg:col-span-8 space-y-6 text-start">
                
                <!-- Section: Chronological Accolade Timeline (Compact padding) -->
                <section class="space-y-4">
                    <h2 class="font-serif text-xl font-bold text-navy border-b border-[var(--silver)]/30 pb-2 flex items-center gap-2">
                        🏆 Accolade Timeline
                    </h2>
                    
                    <div class="relative border-s border-[var(--gold)]/20 ml-2 pl-5 space-y-4 py-1">
                        <?php foreach ($byEdition as $editionKey => $data): ?>
                        <div class="relative group" x-data="{ open: false }">
                            <!-- Timeline Dot Indicator -->
                            <div class="absolute -left-[28px] top-1.5 w-3 h-3 bg-white border border-[var(--gold)] rounded-full group-hover:bg-[var(--gold)] transition-colors duration-300"></div>
                            
                            <div class="bg-white border border-[var(--silver)]/40 rounded-[3px] overflow-hidden shadow-sm transition-all duration-300">
                                <button @click="open = !open"
                                        class="w-full flex items-center justify-between p-4 bg-[#FAF7F2]/40 hover:bg-[#FAF7F2] transition-all cursor-pointer text-start focus:outline-none">
                                    <div class="space-y-0.5">
                                        <span class="text-[9px] uppercase tracking-[1px] text-[var(--gold)] font-bold"><?php echo $data['year']; ?> Edition</span>
                                        <h3 class="font-serif text-base font-bold text-navy"><?php echo htmlspecialchars($data['name']); ?></h3>
                                    </div>
                                    <div class="flex items-center gap-3">
                                        <span class="text-[9px] uppercase font-bold tracking-wider text-[var(--navy-light)]">
                                            🏆 <?php echo $data['wins']; ?> Win<?php echo $data['wins'] !== 1 ? 's' : ''; ?> &bull; <?php echo count($data['noms']); ?> Nom<?php echo count($data['noms']) !== 1 ? 's' : ''; ?>
                                        </span>
                                        <span class="text-[var(--gold)] font-bold text-lg transition-transform duration-300" :class="open ? 'rotate-90' : ''">&rsaquo;</span>
                                    </div>
                                </button>

                                <div x-show="open" x-cloak
                                     class="divide-y divide-gray-100 border-t border-gray-100 animate-fade-in bg-white">
                                    <?php foreach ($data['noms'] as $n): ?>
                                    <div class="flex items-center justify-between px-5 py-3 <?php echo $n['isWinner'] ? 'bg-[var(--gold-pale)]/10' : ''; ?>">
                                        <div class="space-y-0.5 min-w-0">
                                            <p class="text-xs font-semibold text-navy truncate"><?php echo htmlspecialchars($n['categoryName']); ?></p>
                                            <p class="text-[11px] text-[var(--navy-light)] truncate"><?php echo htmlspecialchars($n['nomineeText']); ?></p>
                                            <?php if (!empty($n['note'])): ?>
                                                <p class="text-[9px] text-gray-400 italic"><?php echo htmlspecialchars($n['note'] ?? ''); ?></p>
                                            <?php endif; ?>
                                        </div>
                                        <span class="text-[9px] uppercase tracking-wider shrink-0 px-2 py-0.5 rounded-[2px] font-bold <?php echo $n['isWinner'] ? 'bg-[var(--gold)] text-white' : 'bg-gray-100 text-gray-400'; ?>">
                                            <?php echo $n['isWinner'] ? 'Winner' : 'Nominee'; ?>
                                        </span>
                                    </div>
                                    <?php endforeach; ?>
                                </div>
                            </div>
                        </div>
                        <?php endforeach; ?>
                    </div>
                </section>

                <!-- Section: Trailer Media Embed (Compact padding) -->
                <section class="space-y-4">
                    <h2 class="font-serif text-xl font-bold text-navy border-b border-[var(--silver)]/30 pb-2 flex items-center gap-2">
                        🎥 Media Spotlight
                    </h2>
                    
                    <div x-show="loadingTrailer" class="flex flex-col items-center justify-center py-12 bg-white border border-[var(--silver)]/40 rounded-[3px] space-y-2">
                        <span class="animate-spin h-5 w-5 border-2 border-[var(--gold)] border-t-transparent rounded-full"></span>
                        <p class="text-[11px] text-[var(--navy-light)]">Locating movie trailer...</p>
                    </div>

                    <div x-show="!loadingTrailer && resolvedYoutubeId" x-cloak
                         class="bg-white border border-[var(--silver)]/40 rounded-[3px] overflow-hidden shadow-sm">
                        <div class="aspect-video w-full">
                            <iframe class="w-full h-full"
                                    :src="'https://www.youtube.com/embed/' + resolvedYoutubeId"
                                    title="YouTube video player"
                                    frameborder="0"
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                    allowfullscreen></iframe>
                        </div>
                    </div>

                    <div x-show="!loadingTrailer && !resolvedYoutubeId" x-cloak
                         class="flex flex-col items-center justify-center py-12 bg-white border border-[var(--silver)]/40 rounded-[3px] text-[var(--navy-light)]">
                        <p class="text-xs italic">No official media spotlight found for this title.</p>
                    </div>
                </section>
            </div>

            <!-- RIGHT COLUMN: STREAMING & SIDEBAR (35% width) -->
            <div class="lg:col-span-4 space-y-6 text-start">
                
                <!-- Acclaim Rate widget -->
                <?php if ($totalNoms > 0): ?>
                <section class="bg-white border border-[var(--silver)]/40 rounded-[3px] p-5 shadow-sm flex items-center justify-between gap-4">
                    <div class="space-y-0.5">
                        <h3 class="text-[9px] font-bold text-[var(--navy-light)] uppercase tracking-wider">Acclaim Rate</h3>
                        <p class="text-2xl font-serif font-bold text-navy"><?php echo $winPercent; ?>%</p>
                        <p class="text-[11px] text-[var(--navy-light)]"><?php echo $totalWins; ?> wins / <?php echo $totalNoms; ?> noms</p>
                    </div>
                    <div class="relative h-12 w-12 shrink-0">
                        <svg class="h-full w-full" viewBox="0 0 72 72">
                            <circle class="text-gray-100" stroke-width="6" stroke="currentColor" fill="transparent" r="30" cx="36" cy="36" />
                            <circle class="text-[var(--gold)]" stroke-width="6" stroke-linecap="round" stroke="currentColor" fill="transparent" r="30" cx="36" cy="36"
                                    stroke-dasharray="<?php echo $circumference; ?>"
                                    stroke-dashoffset="<?php echo $strokeDashoffset; ?>"
                                    transform="rotate(-90 36 36)" />
                        </svg>
                    </div>
                </section>
                <?php endif; ?>

                <!-- Synopsis synopsis -->
                <?php if (isset($film['synopsis']) && $film['synopsis']): ?>
                <section class="bg-white border border-[var(--silver)]/40 rounded-[3px] p-5 shadow-sm space-y-2">
                    <h3 class="text-xs font-bold text-[var(--navy-light)] uppercase tracking-wider border-b border-gray-100 pb-1.5">Synopsis</h3>
                    <p class="text-xs text-[var(--navy-light)] leading-relaxed"><?php echo htmlspecialchars($film['synopsis']); ?></p>
                </section>
                <?php endif; ?>

                <!-- Streaming Links widget -->
                <section class="bg-white border border-[var(--silver)]/40 rounded-[3px] p-5 shadow-sm space-y-3">
                    <h3 class="text-xs font-bold text-[var(--navy-light)] uppercase tracking-wider border-b border-gray-100 pb-1.5">Where To Watch</h3>
                    <?php if (count($streamingLinks) > 0): ?>
                        <div class="space-y-2">
                            <?php foreach ($streamingLinks as $link): ?>
                            <a href="/awardfilms-api/affiliate/redirect.php?link=<?php echo $link['id']; ?>" target="_blank"
                               class="flex items-center justify-between p-2 rounded-[3px] border border-[var(--silver)] hover:border-[var(--gold)] hover:bg-gray-50 transition-colors text-xs">
                                <span class="font-semibold text-navy"><?php echo htmlspecialchars($link['platform_name']); ?></span>
                                <span class="text-[10px] text-[var(--gold)] font-bold">Watch &rsaquo;</span>
                            </a>
                            <?php endforeach; ?>
                        </div>
                    <?php else: ?>
                        <div class="space-y-1.5">
                            <p class="text-[9px] text-gray-400 font-bold uppercase tracking-wider mb-1">Check availability on:</p>
                            <a href="https://www.justwatch.com/us/search?q=<?php echo urlencode($film['title']); ?>" target="_blank"
                               class="flex items-center justify-between p-2 rounded-[3px] border border-[var(--silver)] hover:border-[var(--gold)] hover:bg-[#FAF7F2]/40 transition-all text-xs font-semibold text-navy">
                                <span class="flex items-center gap-1.5">🔍 JustWatch</span>
                                <span class="text-[9px] text-[var(--gold)] font-bold uppercase tracking-wider">Search ›</span>
                            </a>
                            <a href="https://www.netflix.com/search?q=<?php echo urlencode($film['title']); ?>" target="_blank"
                               class="flex items-center justify-between p-2 rounded-[3px] border border-[var(--silver)] hover:border-[var(--gold)] hover:bg-[#FAF7F2]/40 transition-all text-xs font-semibold text-[#E50914]">
                                <span class="flex items-center gap-1.5">🍿 Netflix</span>
                                <span class="text-[9px] text-[#E50914] font-bold uppercase tracking-wider">Search ›</span>
                            </a>
                            <a href="https://www.amazon.com/s?k=<?php echo urlencode($film['title'] . ' movie'); ?>" target="_blank"
                               class="flex items-center justify-between p-2 rounded-[3px] border border-[var(--silver)] hover:border-[var(--gold)] hover:bg-[#FAF7F2]/40 transition-all text-xs font-semibold text-[#00A8E1]">
                                <span class="flex items-center gap-1.5">🎬 Prime Video</span>
                                <span class="text-[9px] text-[#00A8E1] font-bold uppercase tracking-wider">Search ›</span>
                            </a>
                            <a href="https://play.google.com/store/search?q=<?php echo urlencode($film['title']); ?>&c=movies" target="_blank"
                               class="flex items-center justify-between p-2 rounded-[3px] border border-[var(--silver)] hover:border-[var(--gold)] hover:bg-[#FAF7F2]/40 transition-all text-xs font-semibold text-[#34A853]">
                                <span class="flex items-center gap-1.5">🤖 Google Play</span>
                                <span class="text-[9px] text-[#34A853] font-bold uppercase tracking-wider">Search ›</span>
                            </a>
                        </div>
                    <?php endif; ?>
                </section>

                <!-- Similar Films panel -->
                <?php if (count($similarFilms) > 0): ?>
                <section class="bg-white border border-[var(--silver)]/40 rounded-[3px] p-5 shadow-sm space-y-3">
                    <h3 class="text-xs font-bold text-[var(--navy-light)] uppercase tracking-wider border-b border-gray-100 pb-1.5">Similar Regional Titles</h3>
                    <div class="space-y-3">
                        <?php foreach ($similarFilms as $sf): ?>
                        <a href="/films/<?php echo $sf['filmSlug']; ?>" class="flex gap-2.5 group text-start">
                            <div class="w-8 h-12 bg-gray-50 rounded-[2px] overflow-hidden shrink-0 border border-gray-100">
                                <img src="/img-proxy.php?film=<?php echo $sf['filmId']; ?>" class="w-full h-full object-cover">
                            </div>
                            <div class="min-w-0 flex-1 flex flex-col justify-between py-0.5">
                                <span class="font-serif font-bold text-navy text-xs group-hover:text-[var(--gold)] transition-colors truncate block"><?php echo htmlspecialchars($sf['filmTitle']); ?></span>
                                <span class="text-[9px] text-[var(--navy-light)] uppercase font-semibold">🏆 <?php echo $sf['wins']; ?> Wins &bull; <?php echo $sf['filmYear'] ?: '—'; ?></span>
                            </div>
                        </a>
                        <?php endforeach; ?>
                    </div>
                </section>
                <?php endif; ?>

            </div>

        </div>
    </main>
</div>

<?php 
require_once __DIR__ . '/layouts/footer.php'; 
?>
