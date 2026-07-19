<?php
require_once __DIR__ . '/lib/queries.php';
require_once __DIR__ . '/lib/navigation.php';

// Prepare a lookup of nominations counts
$pdo = DB::connection();
$ceremonyNomCounts = [];
$stmt = $pdo->query('
    SELECT c.slug, COUNT(n.id) as count 
    FROM ceremonies c 
    LEFT JOIN editions e ON e.ceremony_id = c.id 
    LEFT JOIN nominations n ON n.edition_id = e.id 
    GROUP BY c.slug
');
foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $row) {
    $ceremonyNomCounts[$row['slug']] = $row['count'];
}

// Define coordinates for countries represented in NAV_DATA
$countryCoordinates = [
    'USA' => [37.0902, -95.7129],
    'UK' => [55.3781, -3.4360],
    'France' => [46.2276, 2.2137],
    'Italy' => [41.8719, 12.5674],
    'Germany' => [51.1657, 10.4515],
    'Spain' => [40.4637, -3.7492],
    'Nordic' => [62.0000, 15.0000],
    'Sweden' => [60.1282, 18.6435],
    'Denmark' => [56.2639, 9.5018],
    'Norway' => [60.4720, 8.4689],
    'India' => [20.5937, 78.9629],
    'Pakistan' => [30.3753, 69.3451],
    'Bangladesh' => [23.6850, 90.3563],
    'South Korea' => [35.9078, 127.7669],
    'Japan' => [36.2048, 138.2529],
    'China' => [35.8617, 104.1954],
    'Taiwan' => [23.6978, 120.9605],
    'Hong Kong' => [22.3964, 114.1095],
    'Mexico' => [23.6345, -102.5528],
    'Brazil' => [-14.2350, -51.9253],
    'Argentina' => [-38.4161, -63.6167],
    'Iran' => [32.4279, 53.6880],
    'Turkey' => [38.9637, 35.2433],
    'Israel' => [31.0461, 34.8516],
    'Pan-Arab' => [25.0000, 45.0000],
    'Egypt' => [26.8206, 30.8025],
    'UAE' => [23.4241, 53.8478],
    'Morocco' => [31.7917, -7.0926],
    'Nigeria' => [9.0820, 8.6753],
    'Burkina Faso' => [12.2383, -1.5616],
    'Tunisia' => [33.8869, 9.5375],
    'Tanzania' => [-6.3690, 34.8888],
    'South Africa' => [-30.5595, 22.9375],
    'Ghana' => [7.9465, -1.0232],
    'Kenya' => [-0.0236, 37.9062],
    'Uganda' => [1.3733, 32.2903]
];

$pageTitle = "Interactive Global Awards Map";
require_once __DIR__ . '/layouts/head.php';
require_once __DIR__ . '/layouts/header.php';
?>

<!-- Load Leaflet.js CSS & JS via CDN -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
document.addEventListener('alpine:init', () => {
    Alpine.data('mapExplorer', () => ({
        selectedRegion: 'latin-middle-eastern-cinema',
        regions: <?php echo json_encode($NAV_DATA); ?>,
        nomCounts: <?php echo json_encode($ceremonyNomCounts); ?>,
        coords: <?php echo json_encode($countryCoordinates); ?>,
        map: null,
        markers: [],
        
        get activeRegion() {
            return this.regions.find(r => r.slug === this.selectedRegion) || this.regions[0];
        },
        
        init() {
            // Initialize Leaflet Map
            this.map = L.map('map-container').setView([20, 10], 2);
            
            // Use clean CartoDB Positron tile layer matching ivory/parchment design theme
            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; CartoDB',
                subdomains: 'abcd',
                maxZoom: 19
            }).addTo(this.map);
            
            this.renderMarkers();
            
            // Watch for region selection changes to fly map focus
            this.$watch('selectedRegion', () => {
                this.focusMapOnActiveRegion();
            });
            
            // Set initial map focus
            this.focusMapOnActiveRegion();
        },
        
        renderMarkers() {
            // Clear existing markers if any
            this.markers.forEach(m => this.map.removeLayer(m));
            this.markers = [];
            
            // Draw markers for all ceremonies globally
            this.regions.forEach(region => {
                region.industries.forEach(ind => {
                    const country = ind.ceremonies[0]?.country || 'USA';
                    const latLng = this.coords[country] || [0, 0];
                    
                    // Custom gold circle marker
                    const marker = L.circleMarker(latLng, {
                        radius: 8,
                        fillColor: '#B8860B',
                        color: '#1B2A4A',
                        weight: 1.5,
                        opacity: 0.8,
                        fillOpacity: 0.6
                    }).addTo(this.map);
                    
                    // Popup text
                    marker.bindPopup(`
                        <div style='font-family: Playfair Display, serif; font-size: 13px; font-weight: bold;'>
                            ${ind.name}
                        </div>
                        <div style='font-family: Lato, sans-serif; font-size: 11px; color: #666; margin-top: 2px;'>
                            Language: ${ind.language}
                        </div>
                    `);
                    
                    // Click interaction
                    marker.on('click', () => {
                        this.selectedRegion = region.slug;
                        marker.openPopup();
                    });
                    
                    this.markers.push(marker);
                });
            });
        },
        
        focusMapOnActiveRegion() {
            const region = this.activeRegion;
            let bounds = [];
            
            region.industries.forEach(ind => {
                const country = ind.ceremonies[0]?.country || 'USA';
                const latLng = this.coords[country];
                if (latLng) {
                    bounds.push(latLng);
                }
            });
            
            if (bounds.length > 0) {
                this.map.flyToBounds(bounds, { padding: [50, 50], maxZoom: 5 });
            }
        }
    }));
});
</script>

<div class="min-h-screen bg-[#FAFAF8] text-navy py-12 px-6" x-data="mapExplorer">

    <div class="max-w-7xl mx-auto space-y-10">
        
        <!-- HEADER -->
        <div class="text-center space-y-3">
            <span class="eyebrow">Real-Time Interactive Map</span>
            <h1 class="text-4xl md:text-5xl font-serif font-bold tracking-tight">
                Global Awards <em class="gold-italic">Explorer</em>
            </h1>
            <p class="text-sm text-[var(--navy-light)] max-w-xl mx-auto">
                Discover award databases worldwide. Click on the map markers or select a region below to explore regional ceremonies.
            </p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start pt-4">
            
            <!-- LEFT: Real Leaflet Map Container (7 cols width) -->
            <div class="lg:col-span-7 space-y-6">
                <div class="bg-white border border-[#E8E4DC] rounded-xl p-4 shadow-sm flex flex-col items-center">
                    <h3 class="font-serif text-lg font-bold text-navy mb-4 self-start border-b border-[#E8E4DC] pb-2 w-full text-start">Interactive World Map</h3>
                    
                    <!-- Leaflet Container -->
                    <div id="map-container" class="w-full h-[450px] rounded-lg border border-[var(--silver)] z-10"></div>

                    <!-- Region selectors -->
                    <div class="flex flex-wrap gap-2 justify-center mt-6 w-full border-t border-[#E8E4DC] pt-4">
                        <template x-for="r in regions" :key="r.slug">
                            <button @click="selectedRegion = r.slug"
                                    class="text-xs font-bold uppercase tracking-wider px-4 py-2 border transition-all cursor-pointer outline-none"
                                    :class="selectedRegion === r.slug ? 'bg-navy text-white border-transparent shadow-sm' : 'bg-white border-[#E8E4DC] text-[var(--navy-light)] hover:bg-gray-50'">
                                <span x-text="r.label"></span>
                            </button>
                        </template>
                    </div>
                </div>
            </div>

            <!-- RIGHT: Region Ceremonies Details Sidebar (5 cols width) -->
            <div class="lg:col-span-5 space-y-6 text-start">
                <div class="bg-white border border-[#E8E4DC] rounded-xl p-6 shadow-sm space-y-6">
                    
                    <div class="space-y-2">
                        <span class="text-[10px] font-bold uppercase tracking-wider text-gold" x-text="activeRegion.label + ' Region'"></span>
                        <h2 class="font-serif text-2xl font-bold text-navy" x-text="activeRegion.label"></h2>
                        <p class="text-sm text-[var(--navy-light)] leading-relaxed" x-text="activeRegion.description"></p>
                    </div>

                    <div class="space-y-4">
                        <h3 class="text-[10px] font-bold text-[var(--navy-light)] uppercase tracking-wider border-b border-[#E8E4DC] pb-1">Ceremonies &amp; Accolades</h3>
                        
                        <div class="space-y-3 max-h-[350px] overflow-y-auto pr-1">
                            <template x-for="ind in activeRegion.industries" :key="ind.slug">
                                <div class="space-y-2">
                                    <div class="flex items-center gap-2 font-serif text-sm font-bold text-navy mt-3 border-b border-gray-100 pb-1">
                                        <span x-text="ind.flag"></span>
                                        <span x-text="ind.name"></span>
                                        <span class="text-[10px] font-sans text-gray-400 font-normal uppercase tracking-wider" x-text="'(' + ind.language + ')'"></span>
                                    </div>
                                    <div class="grid grid-cols-1 gap-2">
                                        <template x-for="c in ind.ceremonies" :key="c.slug">
                                            <a :href="'/' + activeRegion.slug + '/' + ind.slug + '/' + c.slug"
                                               class="flex items-center justify-between p-3 rounded-lg border border-[var(--silver)] hover:border-[var(--gold)]/40 hover:bg-gray-50 transition-colors">
                                                <div class="space-y-1">
                                                    <span class="text-xs font-semibold text-navy" x-text="c.name"></span>
                                                    <p class="text-[10px] text-gray-400">Est. <span x-text="c.founded"></span></p>
                                                </div>
                                                <span class="text-[10px] text-[var(--gold)] font-bold uppercase tracking-wider" 
                                                      x-text="nomCounts[c.slug] ? nomCounts[c.slug] + ' Noms ›' : 'Explore ›'"></span>
                                            </a>
                                        </template>
                                    </div>
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
