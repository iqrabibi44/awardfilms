<?php
require_once __DIR__ . '/config/DB.php';
require_once __DIR__ . '/lib/queries.php';
require_once __DIR__ . '/lib/navigation.php';

$pdo = DB::connection();

// 1. Top 10 Most Awarded Films
$topAwarded = $pdo->query('
    SELECT title, wins_count, year 
    FROM films 
    WHERE wins_count > 0 
    ORDER BY wins_count DESC 
    LIMIT 10
')->fetchAll(PDO::FETCH_ASSOC);

// 2. Top 10 Most Nominated Films
$topNominated = $pdo->query('
    SELECT title, noms_count, year 
    FROM films 
    WHERE noms_count > 0 
    ORDER BY noms_count DESC 
    LIMIT 10
')->fetchAll(PDO::FETCH_ASSOC);

// 3. Top Ceremonies by Nominations count
$topCeremonies = $pdo->query('
    SELECT c.name, COUNT(n.id) AS nominations_count
    FROM ceremonies c
    INNER JOIN editions e ON e.ceremony_id = c.id
    INNER JOIN nominations n ON n.edition_id = e.id
    GROUP BY c.id, c.name
    ORDER BY nominations_count DESC
    LIMIT 8
')->fetchAll(PDO::FETCH_ASSOC);

// 4. Most Decorated Directors (wins in categories containing Director)
$topDirectors = $pdo->query('
    SELECT n.nominee_text AS director, COUNT(*) AS wins_count
    FROM nominations n
    INNER JOIN categories cat ON n.category_id = cat.id
    WHERE n.is_winner = 1 
      AND (cat.name LIKE "%Director%" OR cat.name LIKE "%Yönetmen%")
      AND n.nominee_text IS NOT NULL AND n.nominee_text != "" AND n.nominee_text != "Director"
    GROUP BY n.nominee_text
    ORDER BY wins_count DESC
    LIMIT 8
')->fetchAll(PDO::FETCH_ASSOC);

// Stats summary
$stats = getStats();

$pageTitle = "AwardFilms Stats & Analytics Dashboard";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';
?>

<!-- Load Chart.js from CDN -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<div class="min-h-screen bg-[#FAFAF8] text-navy py-12 px-6">
    <div class="max-w-7xl mx-auto space-y-12">
        
        <!-- HEADER -->
        <div class="text-center space-y-3">
            <span class="eyebrow">Global Film Statistics</span>
            <h1 class="text-4xl md:text-5xl font-serif font-bold tracking-tight">
                Database <em class="gold-italic">Analytics</em>
            </h1>
            <p class="text-sm text-[var(--navy-light)] max-w-xl mx-auto">
                Explore aggregated insights across all major regional and international cinematic award systems in the database.
            </p>
        </div>

        <!-- HIGHLIGHT METRICS GRID -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="bg-white border border-[#E8E4DC] rounded-xl p-6 shadow-sm text-center space-y-1">
                <span class="text-2xl">🎬</span>
                <p class="text-[10px] font-bold uppercase tracking-wider text-[var(--navy-light)]">Masterpieces Indexed</p>
                <p class="text-3xl font-serif font-bold text-navy"><?php echo number_format($stats['films']); ?></p>
            </div>
            <div class="bg-white border border-[#E8E4DC] rounded-xl p-6 shadow-sm text-center space-y-1">
                <span class="text-2xl">👤</span>
                <p class="text-[10px] font-bold uppercase tracking-wider text-[var(--navy-light)]">Artists Registered</p>
                <p class="text-3xl font-serif font-bold text-navy"><?php echo number_format($stats['persons']); ?></p>
            </div>
            <div class="bg-white border border-[#E8E4DC] rounded-xl p-6 shadow-sm text-center space-y-1">
                <span class="text-2xl">🏆</span>
                <p class="text-[10px] font-bold uppercase tracking-wider text-[var(--navy-light)]">Total Nominations</p>
                <p class="text-3xl font-serif font-bold text-gold"><?php echo number_format($stats['nominations']); ?></p>
            </div>
            <div class="bg-white border border-[#E8E4DC] rounded-xl p-6 shadow-sm text-center space-y-1">
                <span class="text-2xl">🏛️</span>
                <p class="text-[10px] font-bold uppercase tracking-wider text-[var(--navy-light)]">Award Ceremonies</p>
                <p class="text-3xl font-serif font-bold text-navy"><?php echo number_format($stats['ceremonies']); ?></p>
            </div>
        </div>

        <!-- CHARTS GRID -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 pt-4">
            
            <!-- Chart 1: Most Awarded Films -->
            <div class="bg-white border border-[#E8E4DC] rounded-xl p-6 shadow-sm space-y-4">
                <h3 class="font-serif text-lg font-bold text-navy border-b border-[#E8E4DC] pb-2">Most Awarded Masterpieces</h3>
                <div class="relative h-[300px]">
                    <canvas id="chartAwardedFilms"></canvas>
                </div>
            </div>

            <!-- Chart 2: Most Nominated Films -->
            <div class="bg-white border border-[#E8E4DC] rounded-xl p-6 shadow-sm space-y-4">
                <h3 class="font-serif text-lg font-bold text-navy border-b border-[#E8E4DC] pb-2">Most Nominated Titles</h3>
                <div class="relative h-[300px]">
                    <canvas id="chartNominatedFilms"></canvas>
                </div>
            </div>

            <!-- Chart 3: Ceremonies size -->
            <div class="bg-white border border-[#E8E4DC] rounded-xl p-6 shadow-sm space-y-4">
                <h3 class="font-serif text-lg font-bold text-navy border-b border-[#E8E4DC] pb-2">Largest Ceremonies by Nominations</h3>
                <div class="relative h-[300px]">
                    <canvas id="chartCeremonies"></canvas>
                </div>
            </div>

            <!-- Chart 4: Top Directors -->
            <div class="bg-white border border-[#E8E4DC] rounded-xl p-6 shadow-sm space-y-4">
                <h3 class="font-serif text-lg font-bold text-navy border-b border-[#E8E4DC] pb-2">Most Decorated Directors</h3>
                <div class="relative h-[300px]">
                    <canvas id="chartDirectors"></canvas>
                </div>
            </div>

        </div>

    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const navyColor = '#1B2A4A';
    const goldColor = '#B8860B';
    const silverColor = '#C8C0B0';

    // 1. Awarded Films Chart
    new Chart(document.getElementById('chartAwardedFilms').getContext('2d'), {
        type: 'bar',
        data: {
            labels: <?php echo json_encode(array_column($topAwarded, 'title')); ?>,
            datasets: [{
                label: 'Wins count',
                data: <?php echo json_encode(array_column($topAwarded, 'wins_count')); ?>,
                backgroundColor: goldColor,
                borderColor: goldColor,
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, ticks: { color: navyColor, font: { family: 'Lato' } } },
                y: { grid: { display: false }, ticks: { color: navyColor, font: { family: 'Lato' } } }
            }
        }
    });

    // 2. Nominated Films Chart
    new Chart(document.getElementById('chartNominatedFilms').getContext('2d'), {
        type: 'bar',
        data: {
            labels: <?php echo json_encode(array_column($topNominated, 'title')); ?>,
            datasets: [{
                label: 'Nominations count',
                data: <?php echo json_encode(array_column($topNominated, 'noms_count')); ?>,
                backgroundColor: navyColor,
                borderColor: navyColor,
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, ticks: { color: navyColor, font: { family: 'Lato' } } },
                y: { grid: { display: false }, ticks: { color: navyColor, font: { family: 'Lato' } } }
            }
        }
    });

    // 3. Ceremonies Chart
    new Chart(document.getElementById('chartCeremonies').getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: <?php echo json_encode(array_column($topCeremonies, 'name')); ?>,
            datasets: [{
                data: <?php echo json_encode(array_column($topCeremonies, 'nominations_count')); ?>,
                backgroundColor: [
                    '#1B2A4A', '#2E3F5C', '#3A7BD5', '#E91E8C',
                    '#B8860B', '#D4A017', '#E67E22', '#6B1C2A'
                ],
                borderWidth: 2,
                borderColor: '#FFFFFF'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: navyColor, font: { family: 'Lato', size: 10 } }
                }
            }
        }
    });

    // 4. Directors Chart
    new Chart(document.getElementById('chartDirectors').getContext('2d'), {
        type: 'bar',
        data: {
            labels: <?php echo json_encode(array_column($topDirectors, 'director')); ?>,
            datasets: [{
                label: 'Best Director wins',
                data: <?php echo json_encode(array_column($topDirectors, 'wins_count')); ?>,
                backgroundColor: '#6B1C2A',
                borderColor: '#6B1C2A',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, ticks: { color: navyColor, font: { family: 'Lato', size: 10 } } },
                y: { grid: { display: false }, ticks: { color: navyColor, font: { family: 'Lato' } } }
            }
        }
    });
});
</script>

<?php
require_once __DIR__ . '/layouts/footer.php';
?>
