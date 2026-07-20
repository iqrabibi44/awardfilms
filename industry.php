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

<style>
    .slideshow-bg {
        position: absolute;
        inset: 0;
        z-index: 1;
        pointer-events: none;
        opacity: 0.15;
    }
    .slide-item {
        position: absolute;
        inset: 0;
        transition: opacity 1.2s ease-in-out;
        opacity: 0;
        background-position: center;
        background-size: cover;
        background-repeat: no-repeat;
    }
    .slide-item.active {
        opacity: 1;
    }
    .ceremony-card-l1 {
        background: #FFFFFF;
        border: 1px solid rgba(184, 134, 11, 0.12);
        border-radius: 6px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.02);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        overflow: hidden;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 320px;
    }
    .ceremony-card-l1:hover {
        transform: translateY(-4px);
        border-color: var(--gold);
        box-shadow: 0 12px 30px rgba(184, 134, 11, 0.08);
    }
</style>

<div class="min-h-screen bg-[var(--ivory)] text-navy animate-fade-in text-start">
    <!-- Hero / Header Details with Auto-Rotating Background -->
    <div style="border-bottom: 1px solid var(--glass-border); padding: 80px 24px 64px; position: relative; overflow: hidden; background: #FAF7F2;">
        
        <!-- Rotating Slideshow Container -->
        <div class="slideshow-bg">
            <?php foreach ($ind['ceremonies'] as $idx => $c): ?>
                <div class="slide-item <?php echo $idx === 0 ? 'active' : ''; ?>" 
                     style="background-image: url('/img-proxy.php?ceremony=<?php echo $c['slug']; ?>&v=2');"
                     data-slide-index="<?php echo $idx; ?>">
                </div>
            <?php endforeach; ?>
        </div>

        <div class="absolute inset-0 pointer-events-none" style="background: radial-gradient(ellipse at 60% 50%, rgba(184, 134, 11, 0.03) 0%, transparent 70%); z-index: 2;"></div>
        <div class="parchment-watermark" style="z-index: 2;"></div>

        <div style="max-width: 1200px; margin: 0 auto; position: relative; z-index: 3" class="max-w-[1200px] mx-auto relative z-10">
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
                    ✦ <?php echo htmlspecialchars($ind['language']); ?> &middot; <?php echo htmlspecialchars($cat['label']); ?> Cinema ✦
                </p>
            </div>
            
            <h1 style="font-size: clamp(36px, 5vw, 56px); font-family: 'Playfair Display', serif; font-weight: 700; color: var(--navy); margin: 0 0 20px; line-height: 1.1">
                <?php echo htmlspecialchars($ind['name']); ?> <span class="gold-italic">Awards</span>
            </h1>
            
            <div style="display: flex; gap: 8px; flex-wrap: wrap">
                <span class="btn-accent" style="font-size: 12px; padding: 6.5px 20px">
                    🏆 <?php echo count($ind['ceremonies']); ?> Ceremonies
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
        
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 24px">
            <?php foreach ($ind['ceremonies'] as $ceremony): ?>
            <div class="ceremony-card-l1">
                <div>
                    <!-- Header Image block (resolves ceremony logo dynamically) -->
                    <div style="height: 180px; overflow: hidden; border-bottom: 1px solid rgba(0,0,0,0.06); background: #000; position: relative;">
                        <img src="/img-proxy.php?ceremony=<?php echo $ceremony['slug']; ?>&v=2" 
                             alt="<?php echo htmlspecialchars($ceremony['name']); ?>" 
                             style="width: 100%; height: 100%; object-cover: cover; transition: transform 0.5s ease;"
                             class="hover:scale-105">
                        <div style="position: absolute; inset: 0; background: linear-gradient(to top, rgba(0,0,0,0.4) 0%, transparent 50%); pointer-events: none;"></div>
                    </div>

                    <!-- Details Area -->
                    <div style="padding: 20px 24px 10px;">
                        <div style="font-size: 16px; font-family: 'Playfair Display', serif; font-weight: 700; color: var(--navy); margin-bottom: 6px">
                            <?php echo htmlspecialchars($ceremony['name']); ?>
                        </div>
                        <div style="font-size: 11px; font-family: 'Lato', sans-serif; color: var(--navy-light); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                            <?php echo htmlspecialchars($ceremony['country']); ?> &middot; est. <?php echo $ceremony['founded']; ?>
                        </div>
                    </div>
                </div>

                <!-- Explore Link -->
                <div style="padding: 10px 24px 20px; display: flex; justify-content: flex-end; border-top: 1px solid rgba(0,0,0,0.03);">
                    <a href="/<?php echo htmlspecialchars($cat['slug']); ?>/<?php echo htmlspecialchars($ind['slug']); ?>/<?php echo htmlspecialchars($ceremony['slug']); ?>" 
                       style="text-decoration: none; font-size: 11px; font-weight: bold; color: var(--gold); text-transform: uppercase; letter-spacing: 1px;"
                       class="hover:underline">
                        Explore &rarr;
                    </a>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </div>
</div>

<script>
    // Generic auto-rotating background slideshow
    document.addEventListener("DOMContentLoaded", () => {
        const slides = document.querySelectorAll(".slide-item");
        if (slides.length <= 1) return;
        
        let currentIdx = 0;
        setInterval(() => {
            slides[currentIdx].classList.remove("active");
            currentIdx = (currentIdx + 1) % slides.length;
            slides[currentIdx].classList.add("active");
        }, 3000);
    });
</script>

<?php
require_once __DIR__ . '/layouts/footer.php';
?>
