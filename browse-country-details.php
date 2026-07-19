<?php
require_once __DIR__ . '/lib/queries.php';

$countrySlug = $_GET['country'] ?? 'india';
// Normalize slug back to name (e.g. united-states -> United States)
$countryName = ucwords(str_replace('-', ' ', $countrySlug));
if (strtolower($countryName) === 'united states') $countryName = 'United States';
if (strtolower($countryName) === 'united kingdom') $countryName = 'United Kingdom';

$page = isset($_GET['page']) ? (int)$_GET['page'] : 1;
$currentPage = max(1, $page);
$limit = 24;
$offset = ($currentPage - 1) * $limit;

$films = getFilmsByCountry($countryName, $limit, $offset);
$hasMore = count($films) === $limit;

$pageTitle = "Award-Winning Films from " . htmlspecialchars($countryName) . " â€” AwardFilms";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';
?>

<div class="min-h-screen bg-[var(--ivory)] pb-20">
    <div style="background: var(--ivory-deep); border-bottom: 1px solid var(--glass-border); padding: 52px 24px 40px;" class="text-start">
        <div class="max-w-[1280px] mx-auto">
            <nav style="display: flex; gap: 8px; font-size: 13px; color: var(--navy-light); margin-bottom: 20px;">
                <a href="/" style="color: var(--navy-light);">Home</a>
                <span>/</span>
                <a href="/browse" style="color: var(--navy-light);">Browse</a>
                <span>/</span>
                <a href="/browse/country" style="color: var(--navy-light);">Country</a>
                <span>/</span>
                <span style="color: var(--gold);"><?php echo htmlspecialchars($countryName); ?></span>
            </nav>
            <h1 style="font-size: clamp(32px, 5vw, 56px); font-family: 'Playfair Display', serif; font-weight: 700; color: var(--navy); margin: 0 0 12px;">
                ðŸŒ Cinema of <span class="gold-italic"><?php echo htmlspecialchars($countryName); ?></span>
            </h1>
            <p class="font-sans text-[15px] text-[var(--navy-light)] margin-0">
                Explore every award-winning movie produced in <?php echo htmlspecialchars($countryName); ?>.
            </p>
        </div>
    </div>

    <!-- Film list grid -->
    <div class="max-w-[1280px] mx-auto px-6 py-12 text-start">
        <?php if (count($films) === 0): ?>
            <p class="text-sm italic text-gray-400">No films found from this country.</p>
        <?php else: ?>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 24px;">
                <?php foreach ($films as $film): ?>
                <a href="/films/<?php echo htmlspecialchars($film['filmSlug']); ?>" 
                   class="group flex flex-col bg-white border border-[var(--silver)] rounded-[3px] overflow-hidden transition-all duration-200 hover:border-[var(--gold)] hover:shadow-md hover:-translate-y-1 block">
                    <div class="relative aspect-[2/3] bg-gray-50 overflow-hidden">
                        <img src="/img-proxy.php?film=<?php echo $film['filmId']; ?>" alt="" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" loading="lazy">
                        <span style="position: absolute; top: 8px; right: 8px; background: var(--gold); color: var(--ivory); font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 2px;">
                            🏆 <?php echo $film['wins']; ?> Wins
                        </span>
                    </div>
                    <div class="p-4 border-t border-[var(--silver)]/20">
                        <p class="font-serif font-bold text-sm text-navy truncate" title="<?php echo htmlspecialchars($film['filmTitle']); ?>"><?php echo htmlspecialchars($film['filmTitle']); ?></p>
                        <p class="text-xs text-[var(--navy-light)] mt-1"><?php echo $film['filmYear']; ?> &middot; <?php echo $film['noms']; ?> nominations</p>
                    </div>
                </a>
                <?php endforeach; ?>
            </div>

            <!-- Pagination -->
            <div style="display: flex; justify-content: center; gap: 12px; margin-top: 52px;">
                <?php if ($currentPage > 1): ?>
                    <a href="/browse/country/<?php echo $countrySlug; ?>?page=<?php echo $currentPage - 1; ?>" class="btn-secondary">
                        &larr; Previous
                    </a>
                <?php endif; ?>
                <?php if ($hasMore): ?>
                    <a href="/browse/country/<?php echo $countrySlug; ?>?page=<?php echo $currentPage + 1; ?>" class="btn-accent">
                        Next &rarr;
                    </a>
                <?php endif; ?>
            </div>
        <?php endif; ?>
    </div>
</div>

<?php 
require_once __DIR__ . '/layouts/footer.php'; 
?>

