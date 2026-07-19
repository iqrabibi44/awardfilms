<?php
header('Content-Type: text/html; charset=UTF-8');
require_once __DIR__ . '/../lib/translator.php';
Translator::init();
$lang = Translator::getLang();
$rtlLanguages = ['ar', 'he', 'ur', 'fa'];
$dir = in_array($lang, $rtlLanguages) ? 'rtl' : 'ltr';

$isAjax = (isset($_GET['ajax']) || (isset($_SERVER['HTTP_X_REQUESTED_WITH']) && strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest'));
if ($isAjax) {
    $titleToSend = isset($pageTitle) ? $pageTitle . " | AwardFilms" : "AwardFilms — Global Film Awards Database";
    header('X-Page-Title: ' . rawurlencode($titleToSend));
    return;
}
?>
<!DOCTYPE html>
<html lang="<?php echo htmlspecialchars($lang); ?>" dir="<?php echo $dir; ?>" class="scroll-smooth antialiased">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo isset($pageTitle) ? htmlspecialchars($pageTitle) . " | AwardFilms" : "AwardFilms — Global Film Awards Database"; ?></title>
    <meta name="description" content="The definitive database of film award nominations and winners across the Oscars, BAFTA, Golden Globes, Filmfare, and more.">
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    
    <!-- Tailwind CSS (V4) CDN & Alpine.js -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    
    <!-- Custom styling stylesheet -->
    <link rel="stylesheet" href="/assets/css/globals.css">
    
    <!-- Quick styling overrides if needed -->
    <style>
        [x-cloak] { display: none !important; }
    </style>
</head>
<body class="flex min-h-screen flex-col bg-background text-navy font-sans relative">

    <!-- Film Strip Ticker (very top, full width) -->
    <div class="film-strip-ticker" aria-hidden="true">
        <div class="animate-ticker text-[var(--gold-light)] font-serif text-[12px] tracking-[2px] py-1 select-none">
            <?php 
            $ticker_text = "✦ Best Film: Rocky Aur Rani ✦ Best Actor: Shah Rukh Khan — Jawan ✦ Best Actress: Alia Bhatt ✦ Best Director: Karan Johar ✦ ";
            echo str_repeat($ticker_text, 5); 
            ?>
        </div>
    </div>

    <!-- Parchment Watermark (Subtle Trophy Silhouette effect) -->
    <div style="position: fixed; inset: 0; z-index: 0; opacity: 0.035; pointer-events: none; background-image: radial-gradient(circle at center, var(--gold) 0%, transparent 40%); background-size: 120% 120%; background-position: center;" aria-hidden="true"></div>

    <a href="#main-content" class="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:start-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-gold focus:text-white focus:font-bold focus:rounded-md outline-none">
        Skip to main content
    </a>

