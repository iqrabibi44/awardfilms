<?php
require_once __DIR__ . '/lib/queries.php';

$rawCountries = getCountriesWithFilmCounts();

$countryList = [];
foreach ($rawCountries as $r) {
    if ($r['country']) {
        $countryList[] = $r;
    }
}
$countryList = array_slice($countryList, 0, 40);

function countryToSlug($name) {
    return strtolower(preg_replace('/[^a-z0-9]+/i', '-', $name));
}

$pageTitle = "Cinema Universe â€” Award-Winning Films by Country | AwardFilms";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';
?>

<div class="min-h-screen bg-[#1A1A2E] text-white">
    <!-- Hero / Header -->
    <div style="background: linear-gradient(135deg, #0F1117 0%, #12122A 60%, #0F1117 100%); border-bottom: 1px solid rgba(255,255,255,0.06); padding: 52px 24px 40px;" class="text-start">
        <div class="max-w-[1280px] mx-auto">
            <nav aria-label="breadcrumb" style="display: flex; gap: 8px; font-size: 13px; color: #8B8FA8; margin-bottom: 20px;">
                <a href="/" style="color: #8B8FA8;" class="hover:text-[#C9A84C] transition-colors">Home</a>
                <span>/</span>
                <a href="/browse" style="color: #8B8FA8;" class="hover:text-[#C9A84C] transition-colors">Browse</a>
                <span>/</span>
                <span style="color: #F7F4EE;">Cinema Universe</span>
            </nav>
            <h1 style="font-size: clamp(32px, 5vw, 56px); font-weight: 900; color: #F7F4EE; letter-spacing: -0.02em; margin: 0 0 12px; font-family: 'Playfair Display', serif;">
                ðŸŒ Cinema Universe
            </h1>
            <p style="color: #8B8FA8; font-size: 16px; max-width: 540px; margin: 0;">
                Discover every award-winning film categorized by its country of origin.
            </p>
        </div>
    </div>

    <!-- Country Grid Listing -->
    <div class="max-w-[1280px] mx-auto px-6 py-12 text-start">
        <h2 style="font-size: 20px; font-weight: 800; color: #F7F4EE; margin-bottom: 24px; font-family: 'Playfair Display', serif;">
            Top Producing Countries
        </h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px;">
            <?php foreach ($countryList as $row): 
                $slug = countryToSlug($row['country']);
            ?>
            <a href="/browse/country/<?php echo $slug; ?>" 
               class="group flex items-center justify-between bg-[#111122] border border-white/5 rounded-xl px-4 py-3.5 transition-all hover:border-[var(--gold)] hover:bg-[#1A1A2E] block">
                <span class="font-bold text-sm text-[#F7F4EE] group-hover:text-[var(--gold)] transition-colors truncate">
                    <?php echo htmlspecialchars($row['country']); ?>
                </span>
                <span style="font-size: 11px; font-weight: 700; color: #C9A84C; background: rgba(201,168,76,0.1); padding: 2px 8px; border-radius: 10px; flex-shrink: 0; margin-left: 8px;">
                    <?php echo $row['filmCount']; ?>
                </span>
            </a>
            <?php endforeach; ?>
        </div>
    </div>
</div>

<?php 
require_once __DIR__ . '/layouts/footer.php'; 
?>

