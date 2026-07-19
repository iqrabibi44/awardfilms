<?php
require_once __DIR__ . '/lib/queries.php';
require_once __DIR__ . '/lib/navigation.php';

$pageTitle = "My Personal Watchlist & Custom Ballots";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';
?>

<div class="min-h-screen bg-[#FAFAF8] text-navy py-12 px-6" x-data="{
    watchlist: JSON.parse(localStorage.getItem('user_watchlist') || '[]'),
    ballots: JSON.parse(localStorage.getItem('user_ballots') || '{}'),
    newBallotCategory: '',
    newBallotFilm: '',
    
    removeFromWatchlist(id) {
        this.watchlist = this.watchlist.filter(f => f.id !== id);
        localStorage.setItem('user_watchlist', JSON.stringify(this.watchlist));
    },
    
    updateNote(id, note) {
        this.watchlist = this.watchlist.map(f => {
            if (f.id === id) {
                f.note = note;
            }
            return f;
        });
        localStorage.setItem('user_watchlist', JSON.stringify(this.watchlist));
    },
    
    addBallot() {
        if (!this.newBallotCategory.trim() || !this.newBallotFilm.trim()) return;
        this.ballots[this.newBallotCategory.trim()] = this.newBallotFilm.trim();
        localStorage.setItem('user_ballots', JSON.stringify(this.ballots));
        this.newBallotCategory = '';
        this.newBallotFilm = '';
    },
    
    removeBallot(cat) {
        delete this.ballots[cat];
        localStorage.setItem('user_ballots', JSON.stringify(this.ballots));
    }
}">

    <div class="max-w-7xl mx-auto space-y-12">
        
        <!-- HEADER -->
        <div class="text-center space-y-3">
            <span class="eyebrow">Personal Cinema Collection</span>
            <h1 class="text-4xl md:text-5xl font-serif font-bold tracking-tight">
                My <em class="gold-italic">Watchlist</em> &amp; Ballots
            </h1>
            <p class="text-sm text-[var(--navy-light)] max-w-xl mx-auto">
                Manage films you plan to watch, add private commentary notes, and draft your custom mock awards ballots.
            </p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            
            <!-- LEFT COLUMN: WATCHLIST (8 cols) -->
            <div class="lg:col-span-8 space-y-6 text-start">
                <div class="bg-white border border-[#E8E4DC] rounded-xl p-6 shadow-sm space-y-6">
                    <h2 class="font-serif text-2xl font-bold text-navy border-b border-[#E8E4DC] pb-3 flex items-center justify-between">
                        <span>Films to Watch</span>
                        <span class="text-xs bg-[var(--gold-pale)] text-[var(--gold)] font-bold px-2.5 py-1 rounded-full" x-text="watchlist.length + ' Saved'"></span>
                    </h2>

                    <!-- Empty state -->
                    <template x-if="watchlist.length === 0">
                        <div class="text-center py-16 space-y-4">
                            <span class="text-4xl">🎬</span>
                            <p class="text-sm italic text-gray-400">Your watchlist is currently empty.</p>
                            <a href="/films" class="btn-primary py-2 px-6 text-xs font-bold uppercase tracking-wider inline-block">Browse Films →</a>
                        </div>
                    </template>

                    <!-- Watchlist items -->
                    <div class="divide-y divide-[#E8E4DC]">
                        <template x-for="film in watchlist" :key="film.id">
                            <div class="py-6 flex gap-6 items-start first:pt-0 last:pb-0">
                                <!-- Mini Poster -->
                                <div class="relative aspect-[2/3] w-20 shrink-0 bg-[#1A1A2E] border border-[var(--silver)] rounded overflow-hidden">
                                    <img :src="'/img-proxy.php?film=' + film.id" :alt="film.title" class="w-full h-full object-cover">
                                </div>

                                <!-- Movie details -->
                                <div class="flex-grow space-y-3">
                                    <div class="flex items-start justify-between gap-4">
                                        <div class="space-y-1">
                                            <a :href="'/films/' + film.id" class="font-serif text-lg font-bold text-navy hover:text-[var(--gold)] transition-colors" x-text="film.title"></a>
                                            <p class="text-xs text-[var(--navy-light)] font-semibold" x-text="film.year ? 'Released: ' + film.year : ''"></p>
                                        </div>
                                        <button @click="removeFromWatchlist(film.id)"
                                                class="text-xs text-red-600 hover:text-red-800 font-bold uppercase cursor-pointer transition-colors">
                                            Remove
                                        </button>
                                    </div>
                                    
                                    <!-- Persistent private note -->
                                    <div class="flex items-center gap-3">
                                        <input type="text" 
                                               :value="film.note || ''" 
                                               @input="updateNote(film.id, $event.target.value)"
                                               placeholder="Add private note (e.g. 'Highly recommended by friend')..."
                                               class="w-full text-xs bg-[var(--ivory-deep)]/40 hover:bg-[var(--ivory-deep)]/80 focus:bg-white border border-transparent focus:border-[var(--gold)]/40 outline-none px-3 py-1.5 rounded text-navy transition-all placeholder:text-gray-400">
                                    </div>
                                </div>
                            </div>
                        </template>
                    </div>

                </div>
            </div>

            <!-- RIGHT COLUMN: CUSTOM BALLOT MAKER (4 cols) -->
            <div class="lg:col-span-4 space-y-6 text-start">
                <div class="bg-white border border-[#E8E4DC] rounded-xl p-6 shadow-sm space-y-6">
                    <div class="space-y-1">
                        <h2 class="font-serif text-xl font-bold text-navy">Mock Ballots</h2>
                        <p class="text-xs text-[var(--navy-light)] leading-relaxed">
                            Draft your own personal nominations or award winners for this season.
                        </p>
                    </div>

                    <!-- Add Ballot Form -->
                    <form @submit.prevent="addBallot()" class="space-y-3 border-t border-[#E8E4DC] pt-4">
                        <div class="space-y-1">
                            <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--navy-light)]">Award Category</label>
                            <input type="text" x-model="newBallotCategory" placeholder="e.g. Best Film, Best Actor..." 
                                   class="w-full text-xs border border-[var(--silver)] focus:border-[var(--gold)] outline-none px-3 py-2 bg-[var(--ivory)] rounded-[2px]">
                        </div>
                        <div class="space-y-1">
                            <label class="text-[10px] font-bold uppercase tracking-wider text-[var(--navy-light)]">Your Pick / Film</label>
                            <input type="text" x-model="newBallotFilm" placeholder="e.g. Oppenheimer..." 
                                   class="w-full text-xs border border-[var(--silver)] focus:border-[var(--gold)] outline-none px-3 py-2 bg-[var(--ivory)] rounded-[2px]">
                        </div>
                        <button type="submit" class="btn-primary w-full py-2 text-xs font-bold uppercase tracking-wider">
                            Save Pick
                        </button>
                    </form>

                    <!-- Saved Ballots list -->
                    <div class="space-y-3 border-t border-[#E8E4DC] pt-4">
                        <h3 class="text-[10px] font-bold text-[var(--navy-light)] uppercase tracking-wider">My Saved Ballot</h3>
                        
                        <template x-if="Object.keys(ballots).length === 0">
                            <p class="text-xs italic text-gray-400">No mock picks saved yet.</p>
                        </template>

                        <div class="space-y-2">
                            <template x-for="(film, cat) in ballots" :key="cat">
                                <div class="flex items-center justify-between p-3 rounded bg-[var(--ivory-deep)]/40 border border-gray-100">
                                    <div class="space-y-1">
                                        <p class="text-[10px] font-bold uppercase tracking-wider text-gold" x-text="cat"></p>
                                        <p class="text-xs font-semibold text-navy" x-text="film"></p>
                                    </div>
                                    <button @click="removeBallot(cat)" class="text-gray-400 hover:text-red-600 transition-colors">
                                        &times;
                                    </button>
                                </div>
                            </template>
                        </div>
                    </div>

                </div>
            </div>

        </div>

    </div>
</div>

<?php
require_once __DIR__ . '/layouts/footer.php';
?>
