<?php 
require_once __DIR__ . '/../lib/translator.php'; 
$isAjax = (isset($_GET['ajax']) || (isset($_SERVER['HTTP_X_REQUESTED_WITH']) && strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest'));
if ($isAjax) {
    return;
}
?>
</div> <!-- Close #ajax-content-container -->
    <!-- Global Footer -->
    <footer id="about" class="bg-[var(--ivory)] text-[#16213E] border-t border-[#D2CDC0] relative z-10 pt-16 pb-8 mt-auto w-full">
        <div class="mx-auto max-w-7xl px-6">
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-8 mb-12 text-start">
                
                <!-- Column 1: Brand & About -->
                <div class="space-y-4">
                    <a href="/" class="font-serif text-3xl font-bold tracking-wide block transition-colors select-none" style="color: #16213E;" onmouseover="this.style.color='#C9A24B'" onmouseout="this.style.color='#16213E'">
                        AwardFilms<span style="color: #C9A24B;">.</span>
                    </a>
                    <p class="text-sm text-[#5A6478] leading-relaxed pe-4">
                        <?php echo __('The definitive archive of global cinema awards. Discover winners and nominees across the world’s most prestigious film ceremonies.'); ?>
                    </p>
                    <div class="flex items-center gap-4 pt-2">
                        <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" class="text-[#5A6478] hover:text-[#C9A24B] transition-colors" aria-label="Twitter">
                            <svg class="h-5 w-5 fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                            </svg>
                        </a>
                        <a href="https://instagram.com" target="_blank" rel="noopener noreferrer" class="text-[#5A6478] hover:text-[#C9A24B] transition-colors" aria-label="Instagram">
                            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
                                <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                                <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
                            </svg>
                        </a>
                    </div>
                </div>

                <!-- Column 2: Browse -->
                <div class="space-y-4">
                    <h4 class="font-bold text-[#96701A] tracking-wider uppercase text-xs"><?php echo __('Browse'); ?></h4>
                    <ul class="space-y-2 text-sm">
                        <li><a href="/browse" class="text-[#16213E] hover:text-[#C9A24B] transition-colors font-medium"><?php echo __('Ceremonies'); ?></a></li>
                        <li><a href="/films" class="text-[#16213E] hover:text-[#C9A24B] transition-colors font-medium"><?php echo __('Films Database'); ?></a></li>
                        <li><a href="/persons" class="text-[#16213E] hover:text-[#C9A24B] transition-colors font-medium"><?php echo __('People & Artists'); ?></a></li>
                        <li><a href="/search" class="text-[#16213E] hover:text-[#C9A24B] transition-colors font-medium"><?php echo __('Advanced Search'); ?></a></li>
                    </ul>
                </div>

                <!-- Column 3: Categories -->
                <div class="space-y-4">
                    <h4 class="font-bold text-[#96701A] tracking-wider uppercase text-xs"><?php echo __('Categories'); ?></h4>
                    <ul class="space-y-2 text-sm">
                        <li><a href="/browse#decades" class="text-[#16213E] hover:text-[#C9A24B] transition-colors font-medium"><?php echo __('By Decade'); ?></a></li>
                        <li><a href="/browse#genres" class="text-[#16213E] hover:text-[#C9A24B] transition-colors font-medium"><?php echo __('By Genre'); ?></a></li>
                        <li><a href="/browse#countries" class="text-[#16213E] hover:text-[#C9A24B] transition-colors font-medium"><?php echo __('By Country'); ?></a></li>
                    </ul>
                </div>

            </div>

            <div class="border-t border-[#D2CDC0] pt-8 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-[#6E7A90]">
                <p>&copy; <?php echo date('Y'); ?> AwardFilms. <?php echo __('All rights reserved.'); ?></p>
                <div class="flex gap-6">
                    <a href="/privacy" class="hover:text-[#C9A24B] transition-colors"><?php echo __('Privacy Policy'); ?></a>
                    <a href="/terms" class="hover:text-[#C9A24B] transition-colors"><?php echo __('Terms of Service'); ?></a>
                </div>
            </div>

        </div>
    </footer>

    <!-- Alpine.js Cookie Consent Banner -->
    <div x-data="{ 
        show: false, 
        init() {
            if (localStorage.getItem('af_consent') === null) {
                this.show = true;
            }
        },
        accept() {
            localStorage.setItem('af_consent', 'true');
            this.show = false;
        }
    }">
        <div x-show="show" x-cloak
             class="fixed bottom-0 start-0 end-0 z-[100] border-t border-[var(--silver)] bg-[var(--ivory-card)]/95 px-4 py-4 backdrop-blur-md sm:px-6 lg:px-8">
            <div class="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 md:flex-row">
                <p class="text-sm text-[var(--navy-light)]">
                    <?php echo __('We use cookies to improve your experience.'); ?> 
                    <a href="/privacy" class="text-[var(--gold)] hover:underline"><?php echo __('Learn more'); ?></a>.
                </p>
                <button @click="accept" class="rounded-lg bg-[var(--gold)] px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--gold-light)] w-full md:w-auto">
                    <?php echo __('Accept'); ?>
                </button>
            </div>
        </div>
    </div>

    <!-- Single Page AJAX Navigation Script -->
    <script>
    document.addEventListener('DOMContentLoaded', () => {
        const container = document.getElementById('ajax-content-container');
        if (!container) return;

        // Global navigation function
        window.ajaxNavigate = async function(url, pushState = true) {
            try {
                container.style.opacity = '0.6';
                container.style.transition = 'opacity 0.15s ease-in-out';

                const response = await fetch(url, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                if (!response.ok) throw new Error('Failed to fetch page');
                const html = await response.text();

                // Get page title from response header
                const rawTitle = response.headers.get('X-Page-Title');
                if (rawTitle) {
                    document.title = decodeURIComponent(rawTitle);
                }

                // Swap the content
                container.innerHTML = html;
                container.style.opacity = '1';

                // Re-initialize Alpine.js on the new container elements
                if (window.Alpine) {
                    window.Alpine.initTree(container);
                }

                // Scroll to top smoothly
                window.scrollTo({ top: 0, behavior: 'smooth' });

                if (pushState) {
                    history.pushState({ ajax: true, url: url }, '', url);
                }
            } catch (error) {
                console.error('AJAX Navigation Error:', error);
                // Fallback to standard location change
                if (pushState) {
                    window.location.href = url;
                }
            }
        };

        // Intercept local link clicks
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (!link) return;

            const href = link.getAttribute('href');
            if (!href) return;

            // Skip external links, hashes, mailto, etc.
            if (href.startsWith('http') || href.startsWith('//') || href.startsWith('#') || href.startsWith('javascript:') || href.startsWith('mailto:')) {
                return;
            }

            // Skip static asset files
            if (/\.(png|jpg|jpeg|gif|css|js|ico|ttf|woff|woff2|zip|pdf)$/i.test(href)) {
                return;
            }

            e.preventDefault();
            window.ajaxNavigate(href);
        });

        // Handle browser Back/Forward navigation
        window.addEventListener('popstate', (e) => {
            window.ajaxNavigate(window.location.pathname + window.location.search, false);
        });
    });
    </script>
</body>
</html>
