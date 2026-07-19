<?php
require_once __DIR__ . '/../lib/navigation.php';
$isAjax = (isset($_GET['ajax']) || (isset($_SERVER['HTTP_X_REQUESTED_WITH']) && strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest'));
if ($isAjax) {
    return;
}
?>
<!-- Navigation Header with Alpine.js State -->
<div x-data="{ 
    scrolled: false, 
    mobileOpen: false, 
    selectedYear: '2024',
    searchQuery: '',
    results: { films: [], people: [], ceremonies: [] },
    isSearching: false,
    isFocused: false,
    selectedIndex: -1,
    init() {
        window.addEventListener('scroll', () => {
            this.scrolled = window.scrollY > 30;
        }, { passive: true });
        
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
                    this.selectedIndex = -1;
                    this.isFocused = true;
                } catch (e) {
                    console.error(e);
                } finally {
                    this.isSearching = false;
                }
            }, 180);
        });
    },
    handleExplore() {
        const targetUrl = '/search?q=' + encodeURIComponent(this.selectedYear);
        if (window.ajaxNavigate) {
            window.ajaxNavigate(targetUrl);
        } else {
            window.location.href = targetUrl;
        }
    }
}" @click.outside="isFocused = false">

    <!-- Header bar -->
    <header :class="scrolled ? 'shadow-[0_2px_20px_rgba(27,42,74,0.08)] bg-[rgba(250,247,242,0.98)]' : ''" 
            class="fixed top-[32px] start-0 end-0 z-[990] h-[60px] bg-[rgba(250,247,242,0.96)] backdrop-blur-[16px] border-b border-[var(--glass-border)] flex items-center transition-all duration-300">
        
        <div class="mx-auto w-full max-w-[1200px] px-6 flex items-center justify-between gap-4">
            
            <!-- LEFT: Logo -->
            <div class="flex items-center gap-3">
                <div class="h-8 w-[1px] bg-[var(--gold)] opacity-50 hidden sm:block"></div>
                <a href="/" class="flex flex-col select-none group">
                    <span class="font-serif text-[18px] font-bold text-navy tracking-[1.5px] leading-tight transition-colors group-hover:text-[var(--gold)]">
                        AwardFilms<span class="text-[var(--gold)]">.</span>
                    </span>
                    <span class="font-serif text-[8px] uppercase tracking-[2px] text-[var(--gold)] mt-0.5">
                        GLOBAL AWARDS DATABASE
                    </span>
                </a>
            </div>

            <!-- CENTER: Nav links & Dynamic Search Box -->
            <nav class="hidden lg:flex items-center gap-6">
                <a href="/browse" class="font-sans text-[11px] uppercase tracking-[2px] text-navy hover:text-[var(--gold)] transition-colors font-medium">
                    <?php echo __('Ceremonies'); ?>
                </a>
                <a href="/films" class="font-sans text-[11px] uppercase tracking-[2px] text-navy hover:text-[var(--gold)] transition-colors font-medium">
                    <?php echo __('Films'); ?>
                </a>
                <a href="/persons" class="font-sans text-[11px] uppercase tracking-[2px] text-navy hover:text-[var(--gold)] transition-colors font-medium">
                    <?php echo __('Persons'); ?>
                </a>
                <a href="/map.php" class="font-sans text-[11px] uppercase tracking-[2px] text-navy hover:text-[var(--gold)] transition-colors font-medium">
                    <?php echo __('Map'); ?>
                </a>
                <a href="/analytics.php" class="font-sans text-[11px] uppercase tracking-[2px] text-navy hover:text-[var(--gold)] transition-colors font-medium">
                    <?php echo __('Stats'); ?>
                </a>
                <a href="/battles.php" class="font-sans text-[11px] uppercase tracking-[2px] text-navy hover:text-[var(--gold)] transition-colors font-medium">
                    <?php echo __('Battles'); ?>
                </a>
                <a href="/watchlist.php" class="font-sans text-[11px] uppercase tracking-[2px] text-navy hover:text-[var(--gold)] transition-colors font-medium flex items-center gap-1">
                    <span><?php echo __('Watchlist'); ?></span>
                </a>
            </nav>

            <!-- Search input bar -->
            <div class="relative hidden lg:block w-72">
                <div class="flex items-center border border-navy px-3 py-1.5 bg-[var(--ivory)] rounded-[2px] h-[36px]">
                    <svg class="h-4 w-4 text-navy opacity-50 me-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    </svg>
                    <input type="text" placeholder="<?php echo __('Search AwardFilms...'); ?>" 
                           x-model="searchQuery"
                           @focus="isFocused = true"
                           @keydown.enter="if(searchQuery.trim().length > 0) { const target = '/search?q=' + encodeURIComponent(searchQuery.trim()); if (window.ajaxNavigate) { window.ajaxNavigate(target); } else { window.location.href = target; } }"
                           class="w-full text-[12px] bg-transparent outline-none text-navy placeholder:opacity-50">
                    <span x-show="isSearching" class="animate-spin h-3.5 w-3.5 border-2 border-gold border-t-transparent rounded-full ms-1" style="display: none;"></span>
                </div>
                
                <!-- Search Result Dropdown -->
                <div x-show="isFocused && (results.films.length > 0 || results.people.length > 0 || results.ceremonies.length > 0)" x-cloak
                     class="absolute top-10 start-0 end-0 bg-[var(--ivory-card)] border border-[var(--silver)] rounded-[3px] shadow-lg max-h-[350px] overflow-y-auto z-[1000] p-2 flex flex-col gap-2 text-start">
                    
                    <!-- Films Group -->
                    <template x-if="results.films && results.films.length > 0">
                        <div>
                            <div class="px-2 py-1 text-[9px] uppercase font-bold tracking-wider text-[var(--gold)] border-b border-[var(--silver)]/30">🎬 Films</div>
                            <div class="flex flex-col gap-0.5 mt-1">
                                <template x-for="f in results.films" :key="f.url">
                                    <a :href="f.url" @click="isFocused = false; searchQuery = ''" class="flex flex-col px-2 py-1.5 rounded-[2px] hover:bg-[var(--ivory-deep)] transition-colors">
                                        <span class="font-semibold text-[12px] text-navy" x-text="f.title"></span>
                                        <span class="text-[9px] text-[var(--navy-light)]" x-text="f.year"></span>
                                    </a>
                                </template>
                            </div>
                        </div>
                    </template>

                    <!-- People Group -->
                    <template x-if="results.people && results.people.length > 0">
                        <div>
                            <div class="px-2 py-1 text-[9px] uppercase font-bold tracking-wider text-[var(--gold)] border-b border-[var(--silver)]/30">🎭 People</div>
                            <div class="flex flex-col gap-0.5 mt-1">
                                <template x-for="p in results.people" :key="p.url">
                                    <a :href="p.url" @click="isFocused = false; searchQuery = ''" class="flex flex-col px-2 py-1.5 rounded-[2px] hover:bg-[var(--ivory-deep)] transition-colors">
                                        <span class="font-semibold text-[12px] text-navy" x-text="p.name"></span>
                                        <span class="text-[9px] text-[var(--navy-light)]" x-text="p.knownFor"></span>
                                    </a>
                                </template>
                            </div>
                        </div>
                    </template>

                    <!-- Ceremonies Group -->
                    <template x-if="results.ceremonies && results.ceremonies.length > 0">
                        <div>
                            <div class="px-2 py-1 text-[9px] uppercase font-bold tracking-wider text-[var(--gold)] border-b border-[var(--silver)]/30">🏆 Award Shows</div>
                            <div class="flex flex-col gap-0.5 mt-1">
                                <template x-for="c in results.ceremonies" :key="c.url">
                                    <a :href="c.url" @click="isFocused = false; searchQuery = ''" class="flex flex-col px-2 py-1.5 rounded-[2px] hover:bg-[var(--ivory-deep)] transition-colors">
                                        <span class="font-semibold text-[12px] text-navy" x-text="c.name"></span>
                                    </a>
                                </template>
                            </div>
                        </div>
                    </template>
                </div>
            </div>

            <!-- RIGHT: Language, Year Dropdown + Explore button -->
            <div class="hidden sm:flex items-center gap-2">
                <select x-data @change="document.cookie = 'lang=' + $event.target.value + '; path=/'; window.location.reload();"
                        class="font-sans text-[12px] text-navy font-medium border border-[var(--silver)] px-2 py-1.5 bg-[var(--ivory)] hover:border-[var(--gold)] focus:outline-none focus:border-[var(--gold)] transition-colors cursor-pointer rounded-[2px] h-[36px]">
                    <?php 
                    $currentLang = $_COOKIE['lang'] ?? 'en';
                    $languages = [
                        'en' => 'English',
                        'ar' => 'Arabic',
                        'ur' => 'Urdu',
                        'hi' => 'Hindi',
                        'es' => 'Spanish',
                        'fr' => 'French',
                        'de' => 'German',
                        'zh' => 'Chinese'
                    ];
                    foreach ($languages as $code => $name) {
                        $selected = $code === $currentLang ? 'selected' : '';
                        echo "<option value=\"$code\" $selected>$name</option>";
                    }
                    ?>
                </select>

                <select x-model="selectedYear"
                        class="font-sans text-[12px] text-navy font-medium border border-navy px-3 py-1.5 bg-[var(--ivory)] hover:border-[var(--gold)] focus:outline-none focus:border-[var(--gold)] transition-colors cursor-pointer rounded-[2px] h-[36px]">
                    <?php 
                    $years = ["2024", "2020", "2015", "2010", "2005", "2001", "1995", "1985", "1975", "1965", "1954"];
                    foreach ($years as $y) {
                        echo "<option value=\"$y\">$y</option>";
                    }
                    ?>
                </select>
                <button @click="handleExplore" class="btn-primary py-0 px-4 h-[36px] text-[11px] tracking-[1.5px]">
                    Explore →
                </button>
            </div>

            <!-- Mobile Hamburger Trigger -->
            <div class="flex md:hidden items-center">
                <button @click="mobileOpen = true" 
                        class="p-2 text-navy hover:text-[var(--gold)] transition-colors" 
                        aria-label="Toggle Menu">
                    <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                    </svg>
                </button>
            </div>

        </div>
    </header>

    <!-- MOBILE DRAWER MENU (SLIDES FROM RIGHT) -->
    <div x-show="mobileOpen" x-cloak
         class="fixed inset-0 z-[1000] bg-navy/40 backdrop-blur-sm transition-opacity duration-300"
         @click="mobileOpen = false">
        
        <div class="absolute top-0 end-0 bottom-0 w-72 bg-[var(--ivory)] shadow-2xl p-6 transition-transform duration-300 text-start"
             @click.stop>
            
            <div class="flex items-center justify-between border-b border-[var(--silver)] pb-4 mb-6">
                <div class="flex flex-col">
                    <span class="font-serif text-lg font-bold text-navy tracking-[1.5px] leading-tight">
                        AwardFilms<span class="text-[var(--gold)]">.</span>
                    </span>
                    <span class="font-serif text-[8px] uppercase tracking-[2px] text-[var(--gold)] mt-0.5">GLOBAL AWARDS DATABASE</span>
                </div>
                <button @click="mobileOpen = false" class="p-1 rounded-full hover:bg-[var(--ivory-deep)]">
                    <svg class="h-5 w-5 text-navy" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>

            <!-- Mobile search bar -->
            <div class="relative w-full mb-6">
                <div class="flex items-center border border-navy px-3 py-1.5 bg-[var(--ivory)] rounded-[2px] h-[36px]">
                    <input type="text" placeholder="<?php echo __('Search AwardFilms...'); ?>" 
                           x-model="searchQuery"
                           @focus="isFocused = true"
                           @keydown.enter="if(searchQuery.trim().length > 0) { const target = '/search?q=' + encodeURIComponent(searchQuery.trim()); if (window.ajaxNavigate) { window.ajaxNavigate(target); } else { window.location.href = target; } }"
                           class="w-full text-[12px] bg-transparent outline-none text-navy placeholder:opacity-50">
                </div>
                <div x-show="isFocused && (results.films.length > 0 || results.people.length > 0 || results.ceremonies.length > 0)" x-cloak
                     class="absolute top-10 start-0 end-0 bg-[var(--ivory-card)] border border-[var(--silver)] rounded-[3px] shadow-lg max-h-[200px] overflow-y-auto z-[1000] p-2 flex flex-col gap-2 text-start">
                    
                    <!-- Films Group -->
                    <template x-if="results.films && results.films.length > 0">
                        <div>
                            <div class="px-2 py-1 text-[9px] uppercase font-bold tracking-wider text-[var(--gold)] border-b border-[var(--silver)]/30">🎬 Films</div>
                            <div class="flex flex-col gap-0.5 mt-1">
                                <template x-for="f in results.films" :key="f.url">
                                    <a :href="f.url" @click="isFocused = false; searchQuery = ''; mobileOpen = false" class="flex flex-col px-2 py-1 hover:bg-[var(--ivory-deep)] transition-colors">
                                        <span class="font-semibold text-[11px] text-navy" x-text="f.title"></span>
                                        <span class="text-[8px] text-[var(--navy-light)]" x-text="f.year"></span>
                                    </a>
                                </template>
                            </div>
                        </div>
                    </template>

                    <!-- People Group -->
                    <template x-if="results.people && results.people.length > 0">
                        <div>
                            <div class="px-2 py-1 text-[9px] uppercase font-bold tracking-wider text-[var(--gold)] border-b border-[var(--silver)]/30">🎭 People</div>
                            <div class="flex flex-col gap-0.5 mt-1">
                                <template x-for="p in results.people" :key="p.url">
                                    <a :href="p.url" @click="isFocused = false; searchQuery = ''; mobileOpen = false" class="flex flex-col px-2 py-1 hover:bg-[var(--ivory-deep)] transition-colors">
                                        <span class="font-semibold text-[11px] text-navy" x-text="p.name"></span>
                                        <span class="text-[8px] text-[var(--navy-light)]" x-text="p.knownFor"></span>
                                    </a>
                                </template>
                            </div>
                        </div>
                    </template>

                    <!-- Ceremonies Group -->
                    <template x-if="results.ceremonies && results.ceremonies.length > 0">
                        <div>
                            <div class="px-2 py-1 text-[9px] uppercase font-bold tracking-wider text-[var(--gold)] border-b border-[var(--silver)]/30">🏆 Award Shows</div>
                            <div class="flex flex-col gap-0.5 mt-1">
                                <template x-for="c in results.ceremonies" :key="c.url">
                                    <a :href="c.url" @click="isFocused = false; searchQuery = ''; mobileOpen = false" class="flex flex-col px-2 py-1 hover:bg-[var(--ivory-deep)] transition-colors">
                                        <span class="font-semibold text-[11px] text-navy" x-text="c.name"></span>
                                    </a>
                                </template>
                            </div>
                        </div>
                    </template>
                </div>
            </div>

            <div class="flex flex-col gap-6 font-sans text-sm font-semibold">
                <a href="/browse" @click="mobileOpen = false" class="text-navy hover:text-[var(--gold)] py-2 border-b border-[var(--silver)]/40">
                    <?php echo __('Ceremonies'); ?>
                </a>
                <a href="/films" @click="mobileOpen = false" class="text-navy hover:text-[var(--gold)] py-2 border-b border-[var(--silver)]/40">
                    <?php echo __('Films'); ?>
                </a>
                <a href="/persons" @click="mobileOpen = false" class="text-navy hover:text-[var(--gold)] py-2 border-b border-[var(--silver)]/40">
                    <?php echo __('Persons'); ?>
                </a>
                <a href="/map.php" @click="mobileOpen = false" class="text-navy hover:text-[var(--gold)] py-2 border-b border-[var(--silver)]/40">
                    <?php echo __('Map'); ?>
                </a>
                <a href="/analytics.php" @click="mobileOpen = false" class="text-navy hover:text-[var(--gold)] py-2 border-b border-[var(--silver)]/40">
                    <?php echo __('Stats'); ?>
                </a>
                <a href="/battles.php" @click="mobileOpen = false" class="text-navy hover:text-[var(--gold)] py-2 border-b border-[var(--silver)]/40">
                    <?php echo __('Battles'); ?>
                </a>
                <a href="/watchlist.php" @click="mobileOpen = false" class="text-navy hover:text-[var(--gold)] py-2 border-b border-[var(--silver)]/40">
                    <?php echo __('Watchlist'); ?>
                </a>

                <!-- Mobile Year & Language Select -->
                <div class="flex flex-col gap-2 pt-4">
                    <span class="text-[11px] text-[var(--navy-light)] font-bold tracking-[1.5px] uppercase">Select Language</span>
                    <select x-data @change="document.cookie = 'lang=' + $event.target.value + '; path=/'; window.location.reload();"
                            class="w-full text-[13px] text-navy font-semibold border border-[var(--silver)] px-3 py-2 bg-[var(--ivory)] rounded-[2px] mb-2">
                        <?php 
                        foreach ($languages as $code => $name) {
                            $selected = $code === $currentLang ? 'selected' : '';
                            echo "<option value=\"$code\" $selected>$name</option>";
                        }
                        ?>
                    </select>

                    <span class="text-[11px] text-[var(--navy-light)] font-bold tracking-[1.5px] uppercase">Select Year</span>
                    <div class="flex gap-2">
                        <select x-model="selectedYear"
                                class="flex-1 text-[13px] text-navy font-semibold border border-navy px-3 py-2 bg-[var(--ivory)] rounded-[2px]">
                            <?php 
                            foreach ($years as $y) {
                                echo "<option value=\"$y\">$y</option>";
                            }
                            ?>
                        </select>
                        <button @click="mobileOpen = false; handleExplore()" 
                                class="btn-primary py-2 px-4 text-[11px] tracking-[1.5px] whitespace-nowrap">
                            Explore →
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<!-- Space for Header fixing -->
<div class="pt-[92px]"></div>

<div id="ajax-content-container">

