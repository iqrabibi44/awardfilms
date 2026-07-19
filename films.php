<?php
require_once __DIR__ . '/lib/queries.php';

$page = isset($_GET['page']) ? (int)$_GET['page'] : 1;
$currentPage = max(1, $page);
$limit = 48;
$offset = ($currentPage - 1) * $limit;

// Fetch films
$films = listAwardWinningFilms($limit, $offset);
$hasMore = count($films) === $limit;

$pageTitle = "Award-Winning Films â€” Full Database";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';
?>

<div class="min-h-screen bg-[var(--ivory)]">
    <!-- Hero / Header -->
    <div style="background: var(--ivory-deep); border-bottom: 1px solid var(--glass-border); padding: 52px 24px 40px;" class="text-start">
        <div class="max-w-[1280px] mx-auto">
            <nav aria-label="breadcrumb" style="display: flex; gap: 8px; font-size: 13px; color: var(--navy-light); margin-bottom: 20px;">
                <a href="/" style="color: var(--navy-light);" class="hover:text-[var(--gold)] transition-colors">Home</a>
                <span>/</span>
                <span style="color: var(--gold);">Films</span>
            </nav>
            <h1 style="font-size: clamp(32px, 5vw, 56px); font-family: 'Playfair Display', serif; font-weight: 700; color: var(--navy); letter-spacing: -0.01em; margin: 0 0 12px;">
                🎬 Award-Winning <span class="gold-italic">Films</span>
            </h1>
            <p class="font-sans text-[15px] text-[var(--navy-light)] margin-0">
                Every film that has ever won at a major ceremony &mdash; globally
            </p>
        </div>
    </div>

    <!-- Grid Layout -->
    <div class="max-w-[1280px] mx-auto px-6 py-12 text-start">
        <?php if (count($films) === 0): ?>
            <div style="text-align: center; padding: 80px 0;">
                <p style="color: var(--navy-light); fontSize: 18px;">No films found.</p>
            </div>
        <?php else: ?>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 20px;">
                <?php foreach ($films as $film): ?>
                <a href="/films/<?php echo htmlspecialchars($film['filmSlug']); ?>" 
                   class="group flex flex-col bg-[var(--ivory-card)] border border-[var(--silver)] rounded-[3px] overflow-hidden transition-all duration-200 hover:border-[var(--gold)] hover:shadow-[0_8px_24px_rgba(27,42,74,0.12)] hover:-translate-y-1 block">
                    
                    <!-- Poster -->
                    <div style="position: relative; aspect-ratio: 2/3; background: var(--ivory-deep); overflow: hidden;">
                        <img src="/img-proxy.php?film=<?php echo $film['filmId']; ?>" alt="<?php echo htmlspecialchars($film['filmTitle']); ?> poster" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105">
                        
                        <!-- Win badge -->
                        <?php if ($film['wins'] > 0): ?>
                            <span style="position: absolute; top: 8px; right: 8px; background: var(--gold); color: var(--ivory); font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 2px;">
                                🏆 <?php echo $film['wins']; ?>
                            </span>
                        <?php endif; ?>
                    </div>
                    
                    <!-- Info -->
                    <div style="padding: 12px 12px 14px; border-top: 1px solid var(--silver);">
                        <p style="font-family: 'Playfair Display', serif; font-size: 15px; font-weight: 700; color: var(--navy); margin: 0 0 6px; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                            <?php echo htmlspecialchars($film['filmTitle']); ?>
                        </p>
                        <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--navy-light); font-family: 'Lato', sans-serif;">
                            <span><?php echo $film['filmYear'] ?: "â€”"; ?></span>
                            <span><?php echo $film['noms']; ?> nom<?php echo $film['noms'] !== 1 ? "s" : ""; ?></span>
                        </div>
                    </div>
                </a>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>

        <!-- Pagination -->
        <div style="display: flex; justify-content: center; gap: 12px; margin-top: 52px;">
            <?php if ($currentPage > 1): ?>
                <a href="/films?page=<?php echo $currentPage - 1; ?>" class="btn-secondary">
                    â† Previous
                </a>
            <?php endif; ?>
            <?php if ($hasMore): ?>
                <a href="/films?page=<?php echo $currentPage + 1; ?>" class="btn-accent">
                    Next →
                </a>
            <?php endif; ?>
        </div>
    </div>
</div>

<?php 
require_once __DIR__ . '/layouts/footer.php'; 
?>

