<?php
require_once __DIR__ . '/lib/queries.php';

// Fetch featured lists
$recentFilms = getFilmsByDecade(2020, 2029, 24, 0);
$ninetiesFilms = getFilmsByDecade(1990, 1999, 24, 0);
$actionFilms = getFilmsByGenre("Action", 24, 0);
$dramaFilms = getFilmsByGenre("Drama", 24, 0);
$indianFilms = getFilmsByCountry("India", 24, 0);
$usFilms = getFilmsByCountry("United States", 24, 0);

$decades = ["1920s", "1930s", "1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"];
$genres = ["Action", "Drama", "Comedy", "Documentary", "Animation", "Thriller", "Romance", "Horror", "Sci-Fi", "Foreign Language"];
$countries = ["United States", "United Kingdom", "France", "India", "Japan", "South Korea", "Italy", "Germany", "Spain", "Pakistan"];

function renderFilmRow($title, $subtitle, $films, $viewAllHref) {
    if (count($films) === 0) return;
    ?>
    <section class="max-w-7xl mx-auto px-6 mb-12 text-start">
        <div class="flex items-end justify-between border-b border-[var(--silver)]/45 pb-3 mb-6">
            <div>
                <h2 class="font-serif text-2xl font-bold text-navy leading-none"><?php echo htmlspecialchars($title); ?></h2>
                <p class="text-xs text-[var(--navy-light)] font-bold mt-1.5"><?php echo htmlspecialchars($subtitle); ?></p>
            </div>
            <a href="<?php echo $viewAllHref; ?>" class="text-xs font-bold text-[var(--gold)] hover:underline uppercase tracking-wider whitespace-nowrap">View All &rsaquo;</a>
        </div>
        
        <!-- Horizontal Scrollable Film Row -->
        <div class="flex gap-5 overflow-x-auto pb-4 scrollbar-thin">
            <?php foreach ($films as $film): ?>
            <a href="/films/<?php echo htmlspecialchars($film['filmSlug']); ?>" 
               class="group shrink-0 w-36 flex flex-col bg-white border border-[var(--silver)] rounded-[3px] overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:border-[var(--gold)]/40 hover:shadow-md block">
                <div class="relative aspect-[2/3] w-full bg-[var(--ivory-deep)] overflow-hidden">
                    <img src="/img-proxy.php?film=<?php echo $film['filmId']; ?>" alt="" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" loading="lazy">
                    <span style="position: absolute; top: 6px; right: 6px; background: var(--gold); color: var(--ivory); font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 2px;">
                        🏆 <?php echo $film['wins']; ?>
                    </span>
                </div>
                <div class="p-3 text-start border-t border-[var(--silver)]/20">
                    <p class="font-serif font-bold text-xs text-navy truncate leading-snug" title="<?php echo htmlspecialchars($film['filmTitle']); ?>"><?php echo htmlspecialchars($film['filmTitle']); ?></p>
                    <p class="text-[10px] text-[var(--navy-light)] mt-1"><?php echo $film['filmYear'] ?: 'â€”'; ?> &middot; <?php echo $film['noms']; ?> noms</p>
                </div>
            </a>
            <?php endforeach; ?>
        </div>
    </section>
    <?php
}

function renderLinkGrid($items, $basePath) {
    ?>
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        <?php foreach ($items as $item): 
            $slug = strtolower(preg_replace('/[^a-z0-9]+/i', '-', $item));
        ?>
        <a href="/browse/<?php echo $basePath; ?>/<?php echo $slug; ?>" 
           class="group flex items-center justify-between border border-[var(--silver)] bg-white px-4 py-3 rounded-[3px] transition-all hover:-translate-y-0.5 hover:border-[var(--gold)]/50 hover:shadow-md block">
            <span class="font-bold text-xs text-navy group-hover:text-[var(--gold)]"><?php echo htmlspecialchars($item); ?></span>
            <span class="text-[var(--gold)] font-bold transition-transform group-hover:translate-x-1">&rsaquo;</span>
        </a>
        <?php endforeach; ?>
    </div>
    <?php
}

$pageTitle = "Browse Award-Winning Films | Global Cinema Archive";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';
?>

<div class="min-h-screen bg-[var(--ivory)] pb-20">
    <!-- Hero Header -->
    <div style="background: linear-gradient(135deg, var(--ivory) 0%, var(--ivory-deep) 60%, var(--ivory) 100%); border-bottom: 1px solid var(--silver); padding: 60px 24px 48px; position: relative; overflow: hidden;" class="text-start">
        <div class="absolute -top-40 -right-40 w-96 h-96 rounded-full pointer-events-none opacity-20 filter blur-[80px]" style="background: radial-gradient(circle, var(--gold) 0%, transparent 70%);"></div>
        <div class="mx-auto max-w-7xl relative z-10">
            <h1 class="mb-4 text-4xl font-bold font-serif text-navy sm:text-5xl lg:text-6xl tracking-tight leading-tight">
                Explore the <span class="text-[var(--gold)] italic font-serif">Archive</span>
            </h1>
            <p class="max-w-2xl text-base md:text-lg text-[var(--navy-light)] leading-relaxed">
                Browse our vast collection of cinematic excellence. Discover masterpieces through interactive galleries curated by era, genre, and global origins.
            </p>
        </div>
    </div>

    <!-- Featured Horizontal Lists -->
    <div class="mt-10 relative z-20">
        <?php renderFilmRow("The Modern Era", "Award Winners of the 2020s", $recentFilms, "/browse/decade/2020s"); ?>
        <?php renderFilmRow("Action & Adventure", "Heart-Pumping Cinema", $actionFilms, "/browse/genre/action"); ?>
        <?php renderFilmRow("Indian Cinema", "Masterpieces from Bollywood & Beyond", $indianFilms, "/browse/country/india"); ?>
        <?php renderFilmRow("The 1990s", "A Golden Decade of Film", $ninetiesFilms, "/browse/decade/1990s"); ?>
        <?php renderFilmRow("Acclaimed Dramas", "Powerful Storytelling", $dramaFilms, "/browse/genre/drama"); ?>
        <?php renderFilmRow("American Cinema", "Hollywood & Independent Classics", $usFilms, "/browse/country/united-states"); ?>
    </div>

    <!-- Category Directories grid -->
    <div class="mx-auto max-w-7xl px-6 mt-16 text-start">
        <div class="border-t border-[var(--silver)]/40 pt-16">
            <h2 class="text-3xl font-serif font-bold text-navy mb-12 text-center">Browse All Categories</h2>
            
            <div class="space-y-16">
                <section>
                    <div class="flex items-center gap-3 mb-6">
                        <span class="text-xl">📅</span>
                        <h3 class="text-lg font-serif font-bold text-navy">By Decade</h3>
                    </div>
                    <?php renderLinkGrid($decades, "decade"); ?>
                </section>

                <section>
                    <div class="flex items-center gap-3 mb-6">
                        <span class="text-xl">🎬</span>
                        <h3 class="text-lg font-serif font-bold text-navy">By Genre</h3>
                    </div>
                    <?php renderLinkGrid($genres, "genre"); ?>
                </section>

                <section>
                    <div class="flex items-center gap-3 mb-6">
                        <span class="text-xl">ðŸŒ</span>
                        <h3 class="text-lg font-serif font-bold text-navy">By Country</h3>
                    </div>
                    <?php renderLinkGrid($countries, "country"); ?>
                </section>
            </div>
        </div>
    </div>
</div>

<?php 
require_once __DIR__ . '/layouts/footer.php'; 
?>

