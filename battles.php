<?php
require_once __DIR__ . '/lib/queries.php';
require_once __DIR__ . '/lib/navigation.php';

// Fetch two random films with wins_count > 0
$pdo = DB::connection();
$stmt = $pdo->query('
    SELECT id, title, slug, year, country, genre, poster_url, wins_count, noms_count, synopsis
    FROM films 
    WHERE wins_count > 0 AND poster_url IS NOT NULL AND poster_url != ""
    ORDER BY RAND() 
    LIMIT 2
');
$films = $stmt->fetchAll(PDO::FETCH_ASSOC);

// Fallback if not enough films with posters
if (count($films) < 2) {
    $stmt = $pdo->query('
        SELECT id, title, slug, year, country, genre, poster_url, wins_count, noms_count, synopsis
        FROM films 
        WHERE wins_count > 0
        ORDER BY RAND() 
        LIMIT 2
    ');
    $films = $stmt->fetchAll(PDO::FETCH_ASSOC);
}

$pageTitle = "Film Battles â€” Guess the Acclaimed Masterpiece";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';
?>

<script>
document.addEventListener('alpine:init', () => {
    Alpine.data('filmBattles', () => ({
        films: <?php echo json_encode($films); ?>,
        voted: false,
        selectedId: null,
        correctId: null,
        score: parseInt(localStorage.getItem('battle_score') || '0'),
        streak: parseInt(localStorage.getItem('battle_streak') || '0'),
        bestStreak: parseInt(localStorage.getItem('battle_best_streak') || '0'),
        
        init() {
            if (this.films.length < 2) return;
            const f0 = this.films[0];
            const f1 = this.films[1];
            if (f0.wins_count > f1.wins_count) {
                this.correctId = f0.id;
            } else if (f1.wins_count > f0.wins_count) {
                this.correctId = f1.id;
            } else {
                this.correctId = f0.noms_count >= f1.noms_count ? f0.id : f1.id;
            }
        },
        
        vote(id) {
            if (this.voted) return;
            this.voted = true;
            this.selectedId = id;
            
            if (id === this.correctId) {
                this.score++;
                this.streak++;
                if (this.streak > this.bestStreak) {
                    this.bestStreak = this.streak;
                    localStorage.setItem('battle_best_streak', this.bestStreak);
                }
            } else {
                this.streak = 0;
            }
            localStorage.setItem('battle_score', this.score);
            localStorage.setItem('battle_streak', this.streak);
        },
        
        nextRound() {
            window.location.reload();
        },
        
        resetStats() {
            this.score = 0;
            this.streak = 0;
            this.bestStreak = 0;
            localStorage.setItem('battle_score', 0);
            localStorage.setItem('battle_streak', 0);
            localStorage.setItem('battle_best_streak', 0);
        }
    }));
});
</script>

<div class="min-h-screen bg-[#FAFAF8] text-navy py-12 px-6" x-data="filmBattles">

    <div class="max-w-4xl mx-auto text-center space-y-8">
        
        <!-- HEADER -->
        <div class="space-y-3">
            <span class="eyebrow">Interactive Academy Challenge</span>
            <h1 class="text-4xl md:text-5xl font-serif font-bold tracking-tight">
                Film <em class="gold-italic">Battles</em>
            </h1>
            <p class="text-sm text-[var(--navy-light)] max-w-xl mx-auto">
                Test your award season wisdom! Guess which of these two acclaimed masterpieces has accumulated <strong>more total award wins</strong> globally.
            </p>
        </div>

        <!-- SCOREBOARD -->
        <div class="flex items-center justify-center gap-8 bg-white border border-[#E8E4DC] rounded-xl p-4 shadow-sm max-w-md mx-auto">
            <div class="text-center">
                <span class="text-[10px] font-bold uppercase tracking-wider text-[var(--navy-light)]">Total Score</span>
                <p class="text-2xl font-serif font-bold text-navy" x-text="score"></p>
            </div>
            <div class="h-8 w-[1px] bg-[var(--silver)]"></div>
            <div class="text-center">
                <span class="text-[10px] font-bold uppercase tracking-wider text-[var(--navy-light)]">Current Streak</span>
                <p class="text-2xl font-serif font-bold text-gold" x-text="streak"></p>
            </div>
            <div class="h-8 w-[1px] bg-[var(--silver)]"></div>
            <div class="text-center">
                <span class="text-[10px] font-bold uppercase tracking-wider text-[var(--navy-light)]">Best Streak</span>
                <p class="text-2xl font-serif font-bold text-navy" x-text="bestStreak"></p>
            </div>
        </div>

        <!-- BATTLE CARDS -->
        <?php if (count($films) >= 2): ?>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch pt-4">
            
            <template x-for="(film, idx) in films" :key="film.id">
                <div @click="vote(film.id)"
                     class="card-royal cursor-pointer flex flex-col justify-between text-start group h-full focus:outline-none"
                     :class="{
                         'border-[var(--gold)] scale-[1.02] shadow-md': voted && film.id === correctId,
                         'opacity-65 hover:transform-none': voted && film.id !== selectedId && film.id !== correctId,
                         'border-red-500 scale-[0.98]': voted && film.id === selectedId && film.id !== correctId
                     }">
                    
                    <!-- Poster Container -->
                    <div class="relative aspect-[3/4] bg-[#1A1A2E] overflow-hidden">
                        <template x-if="film.poster_url">
                            <img :src="film.poster_url" :alt="film.title" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105">
                        </template>
                        <template x-if="!film.poster_url">
                            <div class="absolute inset-0 flex items-center justify-center text-5xl">🎬</div>
                        </template>
                        
                        <!-- Overlay Result -->
                        <div x-show="voted" x-cloak
                             class="absolute inset-0 bg-black/75 flex flex-col items-center justify-center p-6 text-center text-white animate-fade-in z-20">
                            <span class="text-4xl mb-2" x-text="film.id === correctId ? '🏆' : '❌'"></span>
                            <h3 class="text-xl font-bold uppercase tracking-wider text-[#E8C96D]" x-text="film.id === correctId ? 'More Acclaimed' : 'Underdog'"></h3>
                            <p class="text-2xl font-serif font-bold mt-2" x-text="film.wins_count + ' Award Wins'"></p>
                            <p class="text-xs text-white/70 mt-1" x-text="film.noms_count + ' Nominations'"></p>
                        </div>
                    </div>

                    <!-- Film Details Footer -->
                    <div class="p-6 space-y-2 flex-grow flex flex-col justify-between bg-white">
                        <div class="space-y-1">
                            <h3 class="font-serif text-xl font-bold text-navy group-hover:text-[var(--gold)] transition-colors line-clamp-1" x-text="film.title"></h3>
                            <p class="text-xs font-semibold text-[var(--navy-light)]">
                                <span x-text="film.year"></span> &bull; <span x-text="film.country"></span>
                            </p>
                        </div>
                        <p class="text-xs text-gray-400 mt-2 line-clamp-2" x-text="film.synopsis || 'An acclaimed masterpiece nominated for global awards.'"></p>
                    </div>
                </div>
            </template>

        </div>
        <?php else: ?>
        <div class="py-20 bg-white border border-[#E8E4DC] rounded-xl shadow-sm">
            <p class="text-sm italic text-gray-400">Not enough data available to run battles.</p>
        </div>
        <?php endif; ?>

        <!-- ACTIONS -->
        <div class="flex flex-wrap items-center justify-center gap-4 pt-6">
            <button x-show="voted" @click="nextRound()" x-cloak
                    class="btn-primary py-2.5 px-8 text-xs font-bold uppercase tracking-wider shadow-md hover:bg-gold transition-all duration-300">
                Next Round →
            </button>
            <button @click="resetStats()"
                    class="border border-[var(--silver)] hover:bg-white text-[var(--navy-light)] text-xs font-bold uppercase tracking-wider py-2.5 px-6 rounded-[2px] transition-all">
                Reset Score
            </button>
        </div>

    </div>

</div>

<?php
require_once __DIR__ . '/layouts/footer.php';
?>
