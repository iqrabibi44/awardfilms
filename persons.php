<?php
require_once __DIR__ . '/lib/queries.php';

$page = isset($_GET['page']) ? (int)$_GET['page'] : 1;
$currentPage = max(1, $page);
$limit = 48;
$offset = ($currentPage - 1) * $limit;

// Fetch persons
$persons = listAwardWinningPersons($limit, $offset);
$hasMore = count($persons) === $limit;

$pageTitle = "Award-Winning People â€” AwardFilms Database";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';
?>

<div class="min-h-screen bg-[#FAFAF8] text-[#1C1C1E] animate-fade-in text-start">
    <!-- Hero -->
    <div style="background: linear-gradient(135deg, #FAFAF8 0%, #F4F1EC 60%, #FAFAF8 100%); border-bottom: 1px solid #E8E4DC; padding: 60px 24px 48px;">
        <div class="max-w-[1280px] mx-auto">
            <nav aria-label="breadcrumb" style="display: flex; gap: 8px; font-size: 13px; color: #6B6B6B; margin-bottom: 20px;">
                <a href="/" style="color: #6B6B6B;" class="hover:text-[#C9A84C] transition-colors">Home</a>
                <span>/</span>
                <span style="color: #1C1C1E;">People</span>
            </nav>
            <h1 style="font-size: clamp(32px, 5vw, 56px); font-weight: 700; color: #1A1A2E; fontFamily: var(--font-playfair), serif; margin: 0 0 12px;">
                🎭 Award-Winning People
            </h1>
            <p style="color: #6B6B6B; font-size: 16px; margin: 0;">
                Directors, actors, writers â€” every winner across every ceremony, globally
            </p>
        </div>
    </div>

    <!-- Grid -->
    <div class="max-w-[1280px] mx-auto px-6 py-12">
        <?php if (count($persons) === 0): ?>
            <div style="text-align: center; padding: 80px 0;">
                <p style="color: #6B6B6B; font-size: 18px;">No people found.</p>
            </div>
        <?php else: ?>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 24px;">
                <?php foreach ($persons as $person): ?>
                <a href="/persons/<?php echo htmlspecialchars($person['personSlug']); ?>" 
                   class="group flex flex-col items-center text-center bg-white border border-[#E8E4DC] rounded-[16px] overflow-hidden p-6 shadow-sm transition-all duration-200 hover:border-[#C9A84C]/50 hover:shadow-[0_8px_32px_rgba(201,168,76,0.08)] hover:-translate-y-1 block">
                    
                    <!-- Photo -->
                    <div style="position: relative; width: 96px; height: 96px; border-radius: 50%; overflow: hidden; background: #F4F1EC; border: 2px solid #E8E4DC; margin-bottom: 16px;" 
                         class="group-hover:border-[#C9A84C]/50 transition-colors">
                        <img src="/img-proxy.php?person=<?php echo htmlspecialchars($person['personId']); ?>" alt="<?php echo htmlspecialchars($person['personName']); ?>" class="w-full h-full object-cover object-top">
                    </div>

                    <!-- Name -->
                    <p style="font-size: 14px; font-weight: 700; color: #1C1C1E; margin: 0 0 4px; line-height: 1.3;" 
                       class="group-hover:text-[#C9A84C] transition-colors truncate max-w-full">
                        <?php echo htmlspecialchars($person['personName']); ?>
                    </p>

                    <!-- Nationality -->
                    <?php if ($person['personNationality']): ?>
                        <p style="font-size: 11px; color: #6B6B6B; margin: 0 0 12px;">
                            <?php echo htmlspecialchars($person['personNationality']); ?>
                        </p>
                    <?php endif; ?>

                    <!-- Win badge -->
                    <div style="margin-top: auto;">
                        <span style="display: inline-flex; align-items: center; gap: 4px; background: rgba(201,168,76,0.12); color: #B5860D; font-size: 11px; font-weight: 700; padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(201,168,76,0.2);">
                            ðŸ† <?php echo $person['wins']; ?> win<?php echo $person['wins'] !== 1 ? "s" : ""; ?>
                        </span>
                    </div>
                </a>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>

        <!-- Pagination -->
        <div style="display: flex; justify-content: center; gap: 12px; margin-top: 52px;">
            <?php if ($currentPage > 1): ?>
                <a href="/persons?page=<?php echo $currentPage - 1; ?>" 
                   class="hover:border-[#C9A84C]/50 hover:text-[#C9A84C] transition-all hover:bg-[#F4F1EC] px-6 py-2.5 rounded-[10px] border border-[#E8E4DC] color-[#1C1C1E] font-semibold bg-white text-sm">
                    â† Previous
                </a>
            <?php endif; ?>
            <?php if ($hasMore): ?>
                <a href="/persons?page=<?php echo $currentPage + 1; ?>" 
                   class="hover:opacity-90 transition-opacity px-6 py-2.5 rounded-[10px] bg-gradient-to-br from-[#1A1A2E] to-[#2C5F8A] text-white font-bold text-sm">
                    Next →
                </a>
            <?php endif; ?>
        </div>
    </div>
</div>

<?php 
require_once __DIR__ . '/layouts/footer.php'; 
?>

