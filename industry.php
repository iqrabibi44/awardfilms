<?php
require_once __DIR__ . '/lib/queries.php';
require_once __DIR__ . '/lib/navigation.php';

$supercategorySlug = $_GET['supercategory'] ?? '';
$industrySlug = $_GET['industry'] ?? '';

// Find supercategory
$cat = null;
foreach ($NAV_DATA as $c) {
    if ($c['slug'] === $supercategorySlug) {
        $cat = $c;
        break;
    }
}

// Find industry
$ind = null;
if ($cat) {
    foreach ($cat['industries'] as $i) {
        if ($i['slug'] === $industrySlug) {
            $ind = $i;
            break;
        }
    }
}

if (!$cat || !$ind) {
    http_response_code(404);
    echo "<h1>Industry not found</h1>";
    exit;
}

$pageTitle = $ind['name'] . " Awards";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';

// Calculate earliest founding year
$foundedYears = array_map(fn($c) => $c['founded'], $ind['ceremonies']);
$earliestFounded = count($foundedYears) > 0 ? min($foundedYears) : 'N/A';
?>

<div class="min-h-screen bg-[var(--ivory)] text-navy animate-fade-in">
    <!-- Hero / Header Details -->
    <div style="background: var(--ivory-deep); border-bottom: 1px solid var(--glass-border); padding: 64px 24px 48px; position: relative; overflow: hidden;">
        <div class="absolute inset-0 pointer-events-none" style="background: radial-gradient(ellipse at 60% 50%, rgba(184, 134, 11, 0.04) 0%, transparent 70%);"></div>
        <div class="parchment-watermark"></div>

        <div style="max-width: 1200px; margin: 0 auto; position: relative; z-index: 2" class="max-w-[1200px] mx-auto relative z-10">
            <nav style="display: flex; gap: 8px; align-items: center; margin-bottom: 24px; font-size: 13px; color: var(--navy-light); font-weight: 500; font-family: 'Lato', sans-serif">
                <a href="/" style="color: var(--navy-light); text-decoration: none" class="hover:text-[var(--gold)] transition-colors">Home</a>
                <span>/</span>
                <a href="/cinema/<?php echo htmlspecialchars($cat['slug']); ?>" style="color: var(--navy-light); text-decoration: none" class="hover:text-[var(--gold)] transition-colors"><?php echo htmlspecialchars($cat['label']); ?></a>
                <span>/</span>
                <span style="color: var(--gold)"><?php echo htmlspecialchars($ind['name']); ?></span>
            </nav>
            
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px">
                <div style="font-size: 28px"><?php echo $ind['flag']; ?></div>
                <p class="eyebrow" style="margin: 0">
                    âœ¦ <?php echo htmlspecialchars($ind['language']); ?> &middot; <?php echo htmlspecialchars($cat['label']); ?> Cinema âœ¦
                </p>
            </div>
            
            <h1 style="font-size: clamp(36px, 5vw, 56px); font-family: 'Playfair Display', serif; font-weight: 700; color: var(--navy); margin: 0 0 20px; line-height: 1.1">
                <?php echo htmlspecialchars($ind['name']); ?> <span class="gold-italic">Awards</span>
            </h1>
            
            <div style="display: flex; gap: 8px; flex-wrap: wrap">
                <span class="btn-accent" style="font-size: 12px; padding: 6.5px 20px">
                    ðŸ† <?php echo count($ind['ceremonies']); ?> Ceremonies
                </span>
                <span style="font-size: 12px; color: var(--navy); font-weight: 600; padding: 6px 16px; border: 1px solid var(--silver); border-radius: 3px; background: white; font-family: 'Lato', sans-serif">
                    📅 Since <?php echo $earliestFounded; ?>
                </span>
            </div>
        </div>
    </div>

    <!-- Ceremonies List Grid -->
    <div style="max-width: 1200px; margin: 0 auto; padding: 64px 24px">
        <h2 style="font-size: 24px; font-family: 'Playfair Display', serif; font-weight: 700; color: var(--navy); margin: 0 0 28px">
            All Award <span class="gold-italic">Ceremonies</span>
        </h2>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px">
            <?php foreach ($ind['ceremonies'] as $ceremony): ?>
            <a href="/<?php echo htmlspecialchars($cat['slug']); ?>/<?php echo htmlspecialchars($ind['slug']); ?>/<?php echo htmlspecialchars($ceremony['slug']); ?>" 
               class="card-royal hover-lift flex items-center justify-between p-[20px_24px] text-start">
                <div>
                    <div style="font-size: 16px; font-family: 'Playfair Display', serif; font-weight: 700; color: var(--navy); margin-bottom: 4px">
                        <?php echo htmlspecialchars($ceremony['name']); ?>
                    </div>
                    <div style="font-size: 12px; font-family: 'Lato', sans-serif; color: var(--navy-light)">
                        <?php echo htmlspecialchars($ceremony['country']); ?> &middot; est. <?php echo $ceremony['founded']; ?>
                    </div>
                </div>
                <span style="color: var(--gold); font-size: 18px; flex-shrink: 0" class="arrow-icon">&rarr;</span>
            </a>
            <?php endforeach; ?>
        </div>
    </div>
</div>

<?php
require_once __DIR__ . '/layouts/footer.php';
?>

