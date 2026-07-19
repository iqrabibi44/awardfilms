<?php
$pageTitle = "AwardFilms — Global Film Awards Database";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';
require_once __DIR__ . '/lib/queries.php';

// Fetch initial data directly from database
$stats = getStats();
$recentWinners = getRecentWinners(12);
$trendingFilms = listAwardWinningFilms(6, 0);
$ceremonies = listCeremoniesWithStats();
?>

<!-- Alpine.js Page Controller for Snap-Scroll and Dynamic States -->
<div x-data="{ 
    activeSection: 0,
    activeVideoId: null,
    searchQuery: '',
    results: { films: [], people: [], ceremonies: [] },
    isSearching: false,
    isFocused: false,
    countFilms: 0,
    countCeremonies: 0,
    newsletterEmail: '',
    newsletterMessage: '',
    init() {
        // Stats count-up animation logic
        const targetFilms = <?php echo $stats['films']; ?>;
        const targetCeremonies = <?php echo $stats['ceremonies']; ?>;
        const duration = 1600;
        const startTime = performance.now();

        const animateStats = (now) => {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const ease = 1 - Math.pow(1 - progress, 3); // easeOutCubic

            this.countFilms = Math.floor(ease * targetFilms);
            this.countCeremonies = Math.floor(ease * targetCeremonies);

            if (progress < 1) {
                requestAnimationFrame(animateStats);
            }
        };
        requestAnimationFrame(animateStats);

        // Watch search query with debounce
        let timer;
        this.$watch('searchQuery', value => {
            const query = value.trim();
            if (query.length < 2) {
                this.results = { films: [], people: [], ceremonies: [] };
                this.isFocused = false;
                return;
            }
            this.isSearching = true;
            clearTimeout(timer);
            timer = setTimeout(async () => {
                try {
                    const res = await fetch('/awardfilms-api/suggest.php?q=' + encodeURIComponent(query));
                    const data = await res.json();
                    this.results = data || { films: [], people: [], ceremonies: [] };
                    this.isFocused = true;
                } catch (e) {
                    console.error(e);
                } finally {
                    this.isSearching = false;
                }
            }, 180);
        });

        // Particle background canvas drawing loop
        const canvas = this.$refs.particlesCanvas;
        if (canvas) {
            const ctx = canvas.getContext('2d');
            let width = (canvas.width = canvas.offsetWidth);
            let height = (canvas.height = canvas.offsetHeight);

            window.addEventListener('resize', () => {
                width = canvas.width = canvas.offsetWidth;
                height = canvas.height = canvas.offsetHeight;
            });

            const particles = [];
            for (let i = 0; i < 60; i++) {
                particles.push({
                    x: Math.random() * width,
                    y: Math.random() * height,
                    r: Math.random() * 1.8 + 0.8,
                    d: Math.random() * 60,
                    speed: Math.random() * 0.4 + 0.1,
                    opacity: Math.random() * 0.25 + 0.15,
                });
            }

            const draw = () => {
                ctx.clearRect(0, 0, width, height);
                for (let i = 0; i < particles.length; i++) {
                    const p = particles[i];
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2, true);
                    ctx.fillStyle = 'rgba(184, 134, 11, ' + p.opacity + ')';
                    ctx.fill();

                    p.y -= p.speed;
                    if (p.y < 0) {
                        p.y = height;
                        p.x = Math.random() * width;
                    }
                }
                requestAnimationFrame(draw);
            };
            draw();
        }
    },
    async submitNewsletter() {
        if (!this.newsletterEmail || !this.newsletterEmail.includes('@')) {
            this.newsletterMessage = 'Valid email is required.';
            return;
        }
        try {
            const res = await fetch('/awardfilms-api/newsletter/subscribe.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: this.newsletterEmail })
            });
            const data = await res.json();
            if (data.success) {
                this.newsletterMessage = 'Thank you for subscribing!';
                this.newsletterEmail = '';
            } else {
                this.newsletterMessage = data.message || 'Subscription failed.';
            }
        } catch (e) {
            this.newsletterMessage = 'An error occurred.';
        }
    }
}">

    <main class="flex flex-col">
        
        <!-- SECTION 0: HERO SECTION -->
        <section class="relative min-h-[650px] md:min-h-[750px] flex items-center justify-start overflow-hidden bg-[#0A1227]">
            <!-- Full-Width Background Image (Oscar Statue) -->
            <div class="absolute inset-0 z-0" style="background-image: url('/images/trophy-hero.jpg'); background-size: cover; background-position: left 25%; opacity: 0.55;"></div>
            
            <!-- Soft gradient overlay to ensure text readability while keeping trophy visible -->
            <div class="absolute inset-0 z-0 bg-gradient-to-r from-[#0A1227] via-[#0A1227]/70 to-transparent pointer-events-none"></div>

            <div class="w-full max-w-[1200px] mx-auto px-6 z-10 flex flex-col items-start justify-center relative pt-10">
                <div class="w-full max-w-[650px] space-y-5 text-start">
                    <span class="text-[#D4AF37] text-xs font-bold tracking-[1.5px] uppercase block mb-2">
                        <?php echo __('AwardFilms Archive'); ?>
                    </span>
                    <h1 class="text-5xl md:text-[56px] font-serif leading-[1.1] text-white drop-shadow-md">
                        <?php echo __('The Definitive Database of'); ?> <br>
                        <span class="italic text-[#D4AF37] font-serif"><?php echo __('Global Cinema Awards'); ?></span>
                    </h1>
                    <p class="text-white/80 text-lg leading-relaxed font-light max-w-[550px] pt-1">
                        <?php echo __('Explore winners, nominations, and streaming availability across the Oscars, BAFTA, Filmfare, and international festivals.'); ?>
                    </p>

                    <!-- Search Input Widget -->
                    <div class="relative w-full pt-4 max-w-[550px]">
                        <div class="flex items-center bg-white rounded-full overflow-hidden shadow-2xl h-[60px] p-1 focus-within:ring-2 focus-within:ring-[#D4AF37]/50 transition-all">
                            <input type="text" placeholder="<?php echo __('Search films, actors, directors, awards...'); ?>" 
                                   x-model="searchQuery"
                                   @focus="isFocused = true"
                                   @keydown.enter="if(searchQuery.trim().length > 0) window.ajaxNavigate('/search?q=' + encodeURIComponent(searchQuery.trim()))"
                                   class="flex-1 w-full text-base bg-transparent outline-none text-[#0B122B] placeholder-gray-400 font-sans h-full px-5">
                                   
                            <button @click="if(searchQuery.trim().length > 0) window.ajaxNavigate('/search?q=' + encodeURIComponent(searchQuery.trim()))" 
                                    class="shrink-0 h-full px-8 bg-[#C9A24B] hover:bg-[#D4AF37] text-[#0B122B] font-bold tracking-wide transition-colors rounded-full text-sm">
                                <?php echo __('Search'); ?>
                            </button>
                        </div>
                        
                        <!-- Search dropdown overlay -->
                        <div x-show="isFocused && (results.films.length > 0 || results.people.length > 0 || results.ceremonies.length > 0)" x-cloak
                             class="absolute top-[80px] start-0 end-0 bg-white border border-[#D4AF37]/20 rounded-xl shadow-2xl max-h-[350px] overflow-y-auto z-[200] p-3 flex flex-col gap-2 text-start">
                            
                            <!-- Films Group -->
                            <template x-if="results.films && results.films.length > 0">
                                <div>
                                    <div class="px-2 py-1 text-[9px] uppercase font-bold tracking-wider text-[#D4AF37] border-b border-gray-100">🎬 Films</div>
                                    <div class="flex flex-col gap-0.5 mt-1">
                                        <template x-for="f in results.films" :key="f.url">
                                            <a :href="f.url" @click="isFocused = false; searchQuery = ''" class="flex flex-col px-2 py-1.5 rounded-[4px] hover:bg-gray-50 transition-colors">
                                                <span class="font-semibold text-sm text-[#0B122B]" x-text="f.title"></span>
                                                <span class="text-[10px] text-gray-500" x-text="f.year"></span>
                                            </a>
                                        </template>
                                    </div>
                                </div>
                            </template>

                            <!-- People Group -->
                            <template x-if="results.people && results.people.length > 0">
                                <div>
                                    <div class="px-2 py-1 text-[9px] uppercase font-bold tracking-wider text-[#D4AF37] border-b border-gray-100">🎭 People</div>
                                    <div class="flex flex-col gap-0.5 mt-1">
                                        <template x-for="p in results.people" :key="p.url">
                                            <a :href="p.url" @click="isFocused = false; searchQuery = ''" class="flex flex-col px-2 py-1.5 rounded-[4px] hover:bg-gray-50 transition-colors">
                                                <span class="font-semibold text-sm text-[#0B122B]" x-text="p.name"></span>
                                                <span class="text-[10px] text-gray-500" x-text="p.knownFor"></span>
                                            </a>
                                        </template>
                                    </div>
                                </div>
                            </template>

                            <!-- Ceremonies Group -->
                            <template x-if="results.ceremonies && results.ceremonies.length > 0">
                                <div>
                                    <div class="px-2 py-1 text-[9px] uppercase font-bold tracking-wider text-[#D4AF37] border-b border-gray-100">🏆 Award Shows</div>
                                    <div class="flex flex-col gap-0.5 mt-1">
                                        <template x-for="c in results.ceremonies" :key="c.url">
                                            <a :href="c.url" @click="isFocused = false; searchQuery = ''" class="flex flex-col px-2 py-1.5 rounded-[4px] hover:bg-gray-50 transition-colors">
                                                <span class="font-semibold text-sm text-[#0B122B]" x-text="c.name"></span>
                                            </a>
                                        </template>
                                    </div>
                                </div>
                            </template>
                        </div>
                    </div>

                    <!-- Chips section -->
                    <div class="flex flex-wrap justify-start gap-3 pt-3 text-xs font-semibold items-center">
                        <a href="/search?q=oscars" class="px-4 py-1.5 rounded-full border border-[#D4AF37]/80 text-white/90 hover:bg-[#D4AF37]/10 transition-colors font-sans font-normal">Oscars</a>
                        <a href="/search?q=filmfare" class="px-4 py-1.5 rounded-full border border-[#D4AF37]/80 text-white/90 hover:bg-[#D4AF37]/10 transition-colors font-sans font-normal">Filmfare</a>
                        <a href="/search?q=nollywood" class="px-4 py-1.5 rounded-full border border-[#D4AF37]/80 text-white/90 hover:bg-[#D4AF37]/10 transition-colors font-sans font-normal">Nollywood</a>
                        <a href="/search?q=bafta" class="px-4 py-1.5 rounded-full border border-[#D4AF37]/80 text-white/90 hover:bg-[#D4AF37]/10 transition-colors font-sans font-normal">BAFTA</a>
                    </div>
                </div>
            </div>
        </section>

        <!-- SECTION 0.5: STATS STRIP -->
        <section class="bg-[#10172B] py-14 relative z-20 shadow-xl border-t border-black/20">
            <div class="max-w-[1000px] mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-10 text-center">
                <div class="space-y-3">
                    <span class="text-4xl md:text-5xl font-serif text-[#D4AF37] font-bold block" x-text="countFilms">0</span>
                    <p class="text-[10px] md:text-[11px] text-white/50 uppercase tracking-[3px] font-sans"><?php echo __('Award-winning Films'); ?></p>
                </div>
                <div class="space-y-3 pt-6 md:pt-0">
                    <span class="text-4xl md:text-5xl font-serif text-[#D4AF37] font-bold block" x-text="countCeremonies">0</span>
                    <p class="text-[10px] md:text-[11px] text-white/50 uppercase tracking-[3px] font-sans"><?php echo __('Global Ceremonies'); ?></p>
                </div>
                <div class="space-y-3 pt-6 md:pt-0">
                    <span class="text-4xl md:text-5xl font-serif text-[#D4AF37] font-bold block">2,344</span>
                    <p class="text-[10px] md:text-[11px] text-white/50 uppercase tracking-[3px] font-sans"><?php echo __('Artists Tracked'); ?></p>
                </div>
            </div>
        </section>

        <!-- SECTION 1: REGIONAL VERTICALS -->
        <section class="py-12 md:py-16 bg-[var(--ivory-deep)]">
            <div class="max-w-[1200px] mx-auto px-6 text-center space-y-10">
                <div class="space-y-2">
                    <span class="eyebrow uppercase tracking-[4px] text-[var(--gold)] text-xs font-bold"><?php echo __('Global Reach'); ?></span>
                    <h2 class="text-3xl md:text-5xl font-serif text-[#16213E]"><?php echo __('Explore Cinema'); ?> <span class="gold-italic"><?php echo __('By Region'); ?></span></h2>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    <?php
                    $regions = [
                        ['title' => 'South Asian Cinema', 'slug' => 'south-asian-cinema', 'desc' => 'Bollywood, Lollywood, Tollywood, and more.', 'color' => 'border-pink-500'],
                        ['title' => 'East Asian Cinema', 'slug' => 'east-asian-cinema', 'desc' => 'Korean Hallyu, Japanese masterpieces, and Chinese epics.', 'color' => 'border-blue-500'],
                        ['title' => 'African Cinema', 'slug' => 'african-cinema', 'desc' => 'Nollywood, Ghallywood, and Pan-African film festivals.', 'color' => 'border-green-600'],
                        ['title' => 'Western & European', 'slug' => 'western-european-cinema', 'desc' => 'Hollywood, BAFTA, César, Lola, and Venice.', 'color' => 'border-amber-500'],
                        ['title' => 'Latin & Middle East', 'slug' => 'latin-middle-eastern-cinema', 'desc' => 'Mexican, Brazilian, Argentine, and Arabic cinema.', 'color' => 'border-orange-500']
                    ];
                    foreach ($regions as $r):
                    ?>
                    <a href="/cinema/<?php echo $r['slug']; ?>" class="bg-white p-6 text-start flex flex-col justify-between min-h-[160px] border-s-4 <?php echo $r['color']; ?> rounded-r-lg shadow-sm hover:shadow-md hover:-translate-y-1 transition-all">
                        <div class="space-y-2">
                            <h3 class="text-lg font-serif font-bold text-[#16213E]"><?php echo __($r['title']); ?></h3>
                            <p class="text-sm text-[#9AA6BC] leading-relaxed"><?php echo __($r['desc']); ?></p>
                        </div>
                        <span class="text-xs font-semibold text-[var(--gold)] uppercase tracking-[1px] pt-4 block group-hover:text-[#D4A017]"><?php echo __('Browse ceremonies →'); ?></span>
                    </a>
                    <?php endforeach; ?>
                </div>
            </div>
        </section>

        <!-- SECTION 2: RECENT WINNERS (Horizontal Scroll) -->
        <section class="py-12 md:py-16 bg-[var(--ivory)] overflow-hidden">
            <div class="max-w-[1200px] mx-auto px-6 space-y-8">
                <div class="text-center space-y-2">
                    <span class="eyebrow uppercase tracking-[4px] text-[var(--gold)] text-xs font-bold"><?php echo __('Spotlight Winners'); ?></span>
                    <h2 class="text-3xl md:text-5xl font-serif text-[#16213E]"><?php echo __('Recent'); ?> <span class="gold-italic"><?php echo __('Best Picture'); ?></span> <?php echo __('Recipients'); ?></h2>
                </div>

                <!-- Smooth Horizontal Scroll Carousel -->
                <div class="flex overflow-x-auto snap-x snap-mandatory gap-6 pb-6 pt-2 px-2 -mx-2 hide-scroll" style="scrollbar-width: none; -ms-overflow-style: none;">
                    <?php foreach ($recentWinners as $w): ?>
                    <div class="snap-start shrink-0 w-[160px] md:w-[200px] flex flex-col group relative bg-white border border-[var(--silver)]/40 rounded-lg overflow-hidden shadow-sm hover:shadow-md hover:border-[var(--gold)] transition-all duration-300 hover:-translate-y-1 will-change-transform">
                        <a href="/films/<?php echo $w['filmSlug']; ?>" class="block w-full">
                            <div class="relative aspect-[2/3] w-full bg-gray-50 overflow-hidden">
                                <img src="/img-proxy.php?film=<?php echo $w['filmId']; ?>" alt="<?php echo htmlspecialchars($w['filmTitle']); ?>" loading="lazy" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105">
                            </div>
                            <div class="p-4 bg-white text-start flex flex-col gap-1 border-t border-[var(--silver)]/20">
                                <h4 class="text-sm font-serif font-bold text-[#16213E] truncate" title="<?php echo htmlspecialchars($w['filmTitle']); ?>">
                                    <?php echo htmlspecialchars($w['filmTitle']); ?>
                                </h4>
                                <div class="flex justify-between items-center text-[10px] text-[#9AA6BC] font-semibold uppercase tracking-wider">
                                    <span class="truncate pr-2"><?php echo htmlspecialchars($w['ceremonyName']); ?></span>
                                    <span><?php echo $w['editionYear']; ?></span>
                                </div>
                            </div>
                        </a>
                    </div>
                    <?php endforeach; ?>
                </div>
            </div>
        </section>

        <!-- SECTION 3: TRENDING / POPULAR FILMS -->
        <section class="py-12 md:py-16 bg-[var(--ivory-deep)]">
            <div class="max-w-[1200px] mx-auto px-6 space-y-10">
                <div class="text-center space-y-2">
                    <span class="eyebrow uppercase tracking-[4px] text-[var(--gold)] text-xs font-bold"><?php echo __('Highly Acclaimed'); ?></span>
                    <h2 class="text-3xl md:text-5xl font-serif text-[#16213E]"><?php echo __('Most Decorated'); ?> <span class="gold-italic"><?php echo __('Films'); ?></span></h2>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <?php 
                    $rank = 1;
                    foreach ($trendingFilms as $f): 
                    ?>
                    <a href="/films/<?php echo $f['filmSlug']; ?>" class="bg-white border border-transparent rounded-xl p-4 flex gap-5 shadow-sm hover:shadow-lg hover:border-[var(--gold)] hover:-translate-y-1 transition-all duration-300 relative group overflow-hidden">
                        
                        <!-- Rank Badge -->
                        <div class="absolute top-0 left-0 bg-[#16213E] text-[var(--gold)] font-serif font-bold text-lg w-10 h-10 flex items-center justify-center rounded-br-xl shadow-md z-10">
                            #<?php echo $rank++; ?>
                        </div>

                        <!-- Poster -->
                        <div class="w-24 shrink-0 aspect-[2/3] bg-gray-50 overflow-hidden rounded-md shadow-sm">
                            <img src="/img-proxy.php?film=<?php echo $f['filmId']; ?>" alt="<?php echo htmlspecialchars($f['filmTitle']); ?>" loading="lazy" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500">
                        </div>

                        <!-- Content -->
                        <div class="flex flex-col justify-center flex-1 space-y-3 py-1">
                            <div>
                                <h3 class="text-xl font-serif font-bold text-[#16213E] leading-tight group-hover:text-[var(--gold)] transition-colors line-clamp-2"><?php echo htmlspecialchars($f['filmTitle']); ?></h3>
                                <span class="text-sm text-[#9AA6BC] mt-1 block">
                                    <?php echo $f['filmYear']; ?> &middot; <?php echo htmlspecialchars($f['filmCountry'] ?: 'Global'); ?>
                                </span>
                            </div>
                            <div class="flex gap-4">
                                <div class="flex flex-col">
                                    <span class="text-lg font-bold text-[var(--gold)] leading-none"><?php echo $f['wins']; ?></span>
                                    <span class="text-[9px] uppercase tracking-wider text-[#9AA6BC] font-bold mt-1"><?php echo __('Wins'); ?></span>
                                </div>
                                <div class="w-[1px] bg-[var(--silver)]/40 self-stretch my-1"></div>
                                <div class="flex flex-col">
                                    <span class="text-lg font-bold text-[#16213E] leading-none"><?php echo $f['noms']; ?></span>
                                    <span class="text-[9px] uppercase tracking-wider text-[#9AA6BC] font-bold mt-1"><?php echo __('Noms'); ?></span>
                                </div>
                            </div>
                        </div>
                    </a>
                    <?php endforeach; ?>
                </div>
            </div>
        </section>

        <!-- SECTION 4: NEWSLETTER -->
        <section class="py-12 md:py-16 bg-[#16213E]">
            <div class="max-w-[800px] mx-auto px-6 text-center space-y-10">
                <div class="space-y-6 max-w-md mx-auto pt-2">
                    <div class="space-y-2">
                        <h2 class="text-2xl md:text-3xl font-serif text-white"><?php echo __('Subscribe to'); ?> <span class="gold-italic text-[#D4AF37] font-serif italic"><?php echo __('Our Newsletter'); ?></span></h2>
                        <p class="text-sm text-[#9AA6BC]"><?php echo __('Get daily digests of global award winner announcements and film ceremony recaps.'); ?></p>
                    </div>
                    
                    <form @submit.prevent="submitNewsletter" class="flex gap-2 w-full max-w-sm mx-auto h-[48px]">
                        <input type="email" placeholder="name@example.com" 
                               x-model="newsletterEmail"
                               class="flex-1 px-4 bg-white rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#D4AF37] transition-all h-full text-[#0B122B] placeholder-[#9AA6BC]">
                        <button type="submit" class="px-6 rounded-lg text-sm font-bold tracking-wider transition-all uppercase active:scale-[0.97] h-full flex items-center justify-center"
                                style="background-color: #D4AF37; color: #0B122B;"
                                onmouseover="this.style.backgroundColor='#F3C746'"
                                onmouseout="this.style.backgroundColor='#D4AF37'"><?php echo __('Subscribe'); ?></button>
                    </form>
                    <p x-show="newsletterMessage" x-cloak class="text-xs font-bold text-[#D4AF37] mt-2" x-text="newsletterMessage"></p>
                </div>
            </div>
        </section>

    </main>
</div>

<!-- Hide scrollbar class for horizontal carousels -->
<style>
.hide-scroll::-webkit-scrollbar {
    display: none;
}
.hide-scroll {
    -ms-overflow-style: none;
    scrollbar-width: none;
}
</style>

<?php 
require_once __DIR__ . '/layouts/footer.php'; 
?>
