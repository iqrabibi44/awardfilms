<?php
require_once __DIR__ . '/lib/queries.php';
require_once __DIR__ . '/lib/navigation.php';

$supercategorySlug = $_GET['supercategory'] ?? '';

// Find supercategory
$cat = null;
foreach ($NAV_DATA as $c) {
    if ($c['slug'] === $supercategorySlug) {
        $cat = $c;
        break;
    }
}

if (!$cat) {
    http_response_code(404);
    echo "<h1>Category not found</h1>";
    exit;
}

$pageTitle = $cat['label'] . " Cinema Awards";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';

$totalCeremonies = 0;
foreach ($cat['industries'] as $ind) {
    $totalCeremonies += count($ind['ceremonies']);
}
?>

<div class="min-h-screen bg-[var(--ivory)] text-navy animate-fade-in">
    <!-- Breadcrumb & Hero -->
    <div style="background: var(--ivory-deep); border-bottom: 1px solid var(--glass-border); padding: 64px 24px 48px; position: relative; overflow: hidden;">
        <div class="absolute inset-0 pointer-events-none" style="background: radial-gradient(ellipse at 60% 50%, rgba(184, 134, 11, 0.04) 0%, transparent 70%);"></div>
        <div class="parchment-watermark"></div>

        <div style="maxWidth: "1200px", margin: "0 auto", position: "relative", zIndex: 2" class="max-w-[1200px] mx-auto relative z-10">
            <nav style="display: flex; gap: 8px; align-items: center; margin-bottom: 24px; font-size: 13px; color: var(--navy-light); font-weight: 500; font-family: 'Lato', sans-serif">
                <a href="/" style="color: var(--navy-light); text-decoration: none" class="hover:text-[var(--gold)] transition-colors">Home</a>
                <span>/</span>
                <span style="color: var(--gold)"><?php echo htmlspecialchars($cat['label']); ?> Cinema</span>
            </nav>
            
            <p class="eyebrow mb-2">âœ¦ Cinema Region âœ¦</p>
            
            <h1 style="font-size: clamp(36px, 5vw, 56px); font-family: 'Playfair Display', serif; font-weight: 700; color: var(--navy); margin: 0 0 16px; line-height: 1.1">
                <?php echo htmlspecialchars($cat['label']); ?> <span class="gold-italic">Cinema</span>
            </h1>
            
            <p class="body-text" style="max-width: 700px; margin: 0 0 28px">
                <?php echo htmlspecialchars($cat['description']); ?>
            </p>
            
            <div style="display: flex; gap: 8px; flex-wrap: wrap">
                <span style="font-size: 12px; color: var(--navy); font-weight: 600; padding: 6px 16px; border: 1px solid var(--silver); border-radius: 3px; background: white; font-family: 'Lato', sans-serif">
                    🎬 <?php echo count($cat['industries']); ?> Industries
                </span>
                <span class="btn-accent" style="font-size: 12px; padding: 6.5px 20px">
                    ðŸ† <?php echo $totalCeremonies; ?> Ceremonies
                </span>
            </div>
        </div>
    </div>

    <!-- Industry Grid -->
    <div style="max-width: 1200px; margin: 0 auto; padding: 64px 24px">
        <h2 style="font-size: 24px; font-family: 'Playfair Display', serif; font-weight: 700; color: var(--navy); margin: 0 0 28px">
            All <span class="gold-italic">Industries</span>
        </h2>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px">
            <?php foreach ($cat['industries'] as $ind): ?>
            <a href="/cinema/<?php echo htmlspecialchars($cat['slug']); ?>/<?php echo htmlspecialchars($ind['slug']); ?>" 
               class="card-royal hover-lift block p-[28px] text-start">
                <div style="font-size: 32px; margin-bottom: 12px"><?php echo $ind['flag']; ?></div>
                <div style="font-size: 20px; font-family: 'Playfair Display', serif; font-weight: 700; color: var(--navy); margin-bottom: 4px">
                    <?php echo htmlspecialchars($ind['name']); ?>
                </div>
                <div style="font-size: 11px; font-family: 'Cormorant Garamond', serif; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: var(--gold); margin-bottom: 16px">
                    <?php echo htmlspecialchars($ind['language']); ?>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 6px">
                    <?php 
                    $slice = array_slice($ind['ceremonies'], 0, 4);
                    foreach ($slice as $c): 
                    ?>
                    <span style="font-size: 11px; font-family: 'Lato', sans-serif; padding: 4px 10px; background: var(--ivory-deep); border-radius: 2px; color: var(--navy-light); border: 1px solid var(--silver)">
                        <?php echo htmlspecialchars($c['name']); ?>
                    </span>
                    <?php endforeach; ?>
                    
                    <?php if (count($ind['ceremonies']) > 4): ?>
                    <span style="font-size: 11px; font-family: 'Lato', sans-serif; padding: 4px 10px; color: var(--gold); font-weight: 600">
                        +<?php echo count($ind['ceremonies']) - 4; ?> more
                    </span>
                    <?php endif; ?>
                </div>
            </a>
            <?php endforeach; ?>
        </div>
    </div>
</div>

<?php
require_once __DIR__ . '/layouts/footer.php';
?>

