<?php
session_start();
define('ADMIN_PASSWORD', 'admin-awardfilms-2026');
define('ADMIN_USERNAME', 'admin');

// Handle logout
if (isset($_GET['logout'])) {
    unset($_SESSION['admin_logged_in']);
    session_destroy();
    header('Location: admin-dashboard.php');
    exit;
}

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['login'])) {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';
    if ($username === ADMIN_USERNAME && $password === ADMIN_PASSWORD) {
        $_SESSION['admin_logged_in'] = true;
        header('Location: admin-dashboard.php');
        exit;
    } else {
        $error = 'Invalid credentials. Please try again.';
    }
}

$is_logged_in = isset($_SESSION['admin_logged_in']) && $_SESSION['admin_logged_in'] === true;

// Handle File Upload
$import_stats = null;
$import_error = '';

if ($is_logged_in && $_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['csv_file'])) {
    try {
        require_once __DIR__ . '/lib/csv_importer.php';
        
        $file = $_FILES['csv_file'];
        if ($file['error'] !== UPLOAD_ERR_OK) {
            throw new Exception("File upload failed with error code: " . $file['error']);
        }
        
        $fileName = $file['name'];
        $ext = strtolower(pathinfo($fileName, PATHINFO_EXTENSION));
        if ($ext !== 'csv') {
            throw new Exception("Invalid file format. Please upload a .csv file.");
        }
        
        $import_stats = CSVImporter::import($file['tmp_name']);
    } catch (Exception $e) {
        $import_error = $e->getMessage();
    }
}

$pageTitle = "Admin Dashboard";
require_once __DIR__ . '/../layouts/head.php';

if (!$is_logged_in):
?>
<!-- Centered Login Screen -->
<div class="flex-1 flex items-center justify-center py-20 px-6 bg-[var(--ivory)] relative">
    <div style="position: absolute; width: 400px; height: 400px; top: 15%; left: 30%; background: var(--gold-pale); filter: blur(100px); opacity: 0.3; pointer-events: none;"></div>
    
    <div class="w-full max-w-[420px] bg-white border border-[var(--glass-border)] rounded-[4px] shadow-[0_8px_32px_rgba(27,42,74,0.05)] px-8 py-10 relative z-10">
        <div class="text-center mb-8">
            <h1 class="text-2xl font-serif font-bold text-navy tracking-[1.5px] leading-tight">
                AwardFilms<span class="text-[var(--gold)]">.</span>
            </h1>
            <span class="text-[9px] uppercase tracking-[3px] text-[var(--gold)] block mt-1">Admin Portal</span>
        </div>
        
        <?php if ($error): ?>
            <div class="mb-5 bg-red-50 border-s-4 border-red-500 text-red-700 p-3 text-[12px] rounded-[2px]" role="alert">
                <p><?php echo htmlspecialchars($error); ?></p>
            </div>
        <?php endif; ?>
        
        <form method="POST" action="index.php" class="flex flex-col gap-5">
            <div>
                <label for="username" class="block text-[10px] font-bold uppercase tracking-[2px] text-[var(--navy-light)] mb-2">Username</label>
                <input type="text" id="username" name="username" required
                       class="w-full text-[13px] bg-[var(--ivory)] border border-[var(--silver)] focus:border-[var(--gold)] outline-none rounded-[2px] px-4 py-2.5 text-navy font-semibold transition-colors">
            </div>
            
            <div>
                <label for="password" class="block text-[10px] font-bold uppercase tracking-[2px] text-[var(--navy-light)] mb-2">Password</label>
                <input type="password" id="password" name="password" required
                       class="w-full text-[13px] bg-[var(--ivory)] border border-[var(--silver)] focus:border-[var(--gold)] outline-none rounded-[2px] px-4 py-2.5 text-navy font-semibold transition-colors">
            </div>
            
            <button type="submit" name="login"
                    class="mt-3 bg-navy text-white text-[12px] font-bold uppercase tracking-[2px] py-3 px-6 hover:bg-[var(--gold)] hover:text-white transition-all cursor-pointer text-center rounded-[2px]">
                Sign In
            </button>
        </form>
    </div>
</div>
<?php
require_once __DIR__ . '/layouts/footer.php';
exit;
endif;

// If logged in, render Admin Dashboard
require_once __DIR__ . '/../layouts/header.php';
?>
<!-- Main dashboard container -->
<main id="main-content" class="mx-auto w-full max-w-[1200px] px-6 py-12 relative z-10 flex-1">
    
    <!-- Title / Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-[var(--silver)] pb-6 mb-8 gap-4">
        <div>
            <span class="eyebrow mb-1">Administrative Area</span>
            <h1 class="text-3xl font-serif font-bold text-navy">Admin <span class="gold-italic">Dashboard</span></h1>
        </div>
        <div class="flex items-center gap-3">
            <span class="text-[12px] text-[var(--navy-light)] font-semibold">Logged in as: <strong class="text-navy">admin</strong></span>
            <a href="index.php?logout=1" 
               class="text-[10px] font-bold uppercase tracking-[2px] text-[var(--burgundy)] hover:text-[var(--gold)] border border-[var(--burgundy)] hover:border-[var(--gold)] rounded-[2px] px-4 py-2 transition-all">
                Sign Out
            </a>
        </div>
    </div>

    <!-- Main Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <!-- Left 2 Cols: Import Area & Status -->
        <div class="lg:col-span-2 flex flex-col gap-8">
            
            <!-- File Upload Card -->
            <div class="bg-white border border-[var(--glass-border)] rounded-[4px] shadow-[0_4px_24px_rgba(27,42,74,0.03)] p-6 sm:p-8">
                <h2 class="text-xl font-serif font-bold text-navy mb-4">Import Awards & <span class="gold-italic">Nominations</span></h2>
                <p class="text-[13px] text-[var(--navy-light)] mb-6 leading-relaxed">
                    Upload a CSV file containing scraped data to merge into the main database. 
                    The parser performs duplicate checking based on the combination of <strong class="text-navy">Ceremony (Award Name)</strong> and <strong class="text-navy">Year</strong>. 
                    If a record matching these keys already exists, it is dynamically updated (upsert logic).
                </p>

                <!-- Status notifications -->
                <?php if ($import_error): ?>
                    <div class="mb-6 bg-red-50 border-s-4 border-red-500 text-red-700 p-4 text-[12px] rounded-[2px]" role="alert">
                        <p class="font-bold mb-1">Import Failed</p>
                        <p><?php echo htmlspecialchars($import_error); ?></p>
                    </div>
                <?php endif; ?>

                <?php if ($import_stats): ?>
                    <div class="mb-6 bg-green-50 border-s-4 border-green-500 text-green-800 p-5 text-[13px] rounded-[2px]">
                        <h3 class="font-bold text-sm mb-3">✓ Import Completed Successfully!</h3>
                        <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 font-semibold text-[12px]">
                            <div class="bg-white p-3 border border-green-100 rounded-[2px]">
                                <span class="block text-[10px] text-gray-500 uppercase tracking-[1px] mb-1">Parsed Rows</span>
                                <span class="text-lg text-navy"><?php echo $import_stats['total_rows']; ?></span>
                            </div>
                            <div class="bg-white p-3 border border-green-100 rounded-[2px]">
                                <span class="block text-[10px] text-gray-500 uppercase tracking-[1px] mb-1">Skipped Rows</span>
                                <span class="text-lg text-amber-600"><?php echo $import_stats['skipped_rows']; ?></span>
                            </div>
                            <div class="bg-white p-3 border border-green-100 rounded-[2px]">
                                <span class="block text-[10px] text-gray-500 uppercase tracking-[1px] mb-1">Ceremonies</span>
                                <span class="text-lg text-navy">+<?php echo $import_stats['ceremonies_created']; ?></span>
                            </div>
                            <div class="bg-white p-3 border border-green-100 rounded-[2px]">
                                <span class="block text-[10px] text-gray-500 uppercase tracking-[1px] mb-1">Editions</span>
                                <span class="text-lg text-navy">+<?php echo $import_stats['editions_created']; ?></span>
                            </div>
                            <div class="bg-white p-3 border border-green-100 rounded-[2px]">
                                <span class="block text-[10px] text-gray-500 uppercase tracking-[1px] mb-1">Categories</span>
                                <span class="text-lg text-navy">+<?php echo $import_stats['categories_created']; ?></span>
                            </div>
                            <div class="bg-white p-3 border border-green-100 rounded-[2px]">
                                <span class="block text-[10px] text-gray-500 uppercase tracking-[1px] mb-1">Films Created</span>
                                <span class="text-lg text-navy">+<?php echo $import_stats['films_created']; ?></span>
                            </div>
                            <div class="bg-white p-3 border border-green-100 rounded-[2px]">
                                <span class="block text-[10px] text-gray-500 uppercase tracking-[1px] mb-1">Persons Created</span>
                                <span class="text-lg text-navy">+<?php echo $import_stats['persons_created']; ?></span>
                            </div>
                            <div class="bg-white p-3 border border-green-100 rounded-[2px]">
                                <span class="block text-[10px] text-gray-500 uppercase tracking-[1px] mb-1">New Nominations</span>
                                <span class="text-lg text-navy">+<?php echo $import_stats['nominations_inserted']; ?></span>
                            </div>
                            <div class="bg-white p-3 border border-green-100 rounded-[2px]">
                                <span class="block text-[10px] text-gray-500 uppercase tracking-[1px] mb-1">Upserted / Updated</span>
                                <span class="text-lg text-indigo-600">~<?php echo $import_stats['nominations_updated']; ?></span>
                            </div>
                        </div>
                        <?php if (!empty($import_stats['errors'])): ?>
                            <div class="mt-4 border-t border-green-100 pt-3">
                                <span class="block font-bold text-[11px] uppercase tracking-[1px] text-amber-800 mb-2">Process Logs:</span>
                                <div class="max-h-[120px] overflow-y-auto font-mono text-[10px] text-amber-700 bg-amber-50/50 p-2 rounded-[2px] flex flex-col gap-1">
                                    <?php foreach($import_stats['errors'] as $err): ?>
                                        <span><?php echo htmlspecialchars($err); ?></span>
                                    <?php endforeach; ?>
                                </div>
                            </div>
                        <?php endif; ?>
                    </div>
                <?php endif; ?>

                <form action="index.php" method="POST" enctype="multipart/form-data" class="flex flex-col gap-6">
                    <div class="border-2 border-dashed border-[var(--silver)] bg-[var(--ivory)] rounded-[4px] px-8 py-10 text-center transition-all flex flex-col items-center justify-center gap-4 cursor-pointer relative">
                        <input type="file" name="csv_file" accept=".csv" required class="absolute inset-0 opacity-0 cursor-pointer w-full h-full">

                        <div class="h-12 w-12 bg-white rounded-full flex items-center justify-center shadow-sm border border-[var(--glass-border)] text-[var(--gold)]">
                            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                            </svg>
                        </div>
                        
                        <div class="flex flex-col gap-1">
                            <span class="text-sm font-semibold text-navy">Click to browse or drop CSV file here</span>
                            <span class="text-[11px] text-[var(--navy-light)] uppercase tracking-[1px]">CSV format only (Max size 10MB)</span>
                        </div>
                    </div>

                    <button type="submit" 
                            class="bg-navy text-white text-[12px] font-bold uppercase tracking-[2px] py-3.5 px-6 hover:bg-[var(--gold)] hover:text-white transition-all text-center rounded-[2px] cursor-pointer self-start shadow-sm shadow-navy/10">
                        Process & Merge Database
                    </button>
                </form>
            </div>
        </div>

        <!-- Right 1 Col: Sidebar Info & Stats -->
        <div class="flex flex-col gap-8">
            
            <!-- Quick Database Stats Card -->
            <div class="bg-white border border-[var(--glass-border)] rounded-[4px] shadow-[0_4px_24px_rgba(27,42,74,0.03)] p-6">
                <h3 class="text-lg font-serif font-bold text-navy border-b border-[var(--silver)] pb-3 mb-5">Database <span class="gold-italic">Summary</span></h3>
                
                <?php
                require_once __DIR__ . '/lib/queries.php';
                $dbStats = getStats();
                ?>
                <div class="flex flex-col gap-4 font-semibold text-[13px]">
                    <div class="flex justify-between items-center py-2 border-b border-gray-100">
                        <span class="text-[var(--navy-light)]">Total Ceremonies</span>
                        <span class="text-navy text-sm font-bold"><?php echo number_format($dbStats['ceremonies']); ?></span>
                    </div>
                    <div class="flex justify-between items-center py-2 border-b border-gray-100">
                        <span class="text-[var(--navy-light)]">Total Film Records</span>
                        <span class="text-navy text-sm font-bold"><?php echo number_format($dbStats['films']); ?></span>
                    </div>
                    <div class="flex justify-between items-center py-2 border-b border-gray-100">
                        <span class="text-[var(--navy-light)]">Total Nominations</span>
                        <span class="text-navy text-sm font-bold"><?php echo number_format($dbStats['nominations']); ?></span>
                    </div>
                    <div class="flex justify-between items-center py-2">
                        <span class="text-[var(--navy-light)]">Total Industry Persons</span>
                        <span class="text-navy text-sm font-bold"><?php echo number_format($dbStats['persons']); ?></span>
                    </div>
                </div>
            </div>

            <!-- CSV Formatting Guide Card -->
            <div class="bg-white border border-[var(--glass-border)] rounded-[4px] shadow-[0_4px_24px_rgba(27,42,74,0.03)] p-6">
                <h3 class="text-lg font-serif font-bold text-navy border-b border-[var(--silver)] pb-3 mb-4">CSV Schema <span class="gold-italic">Guide</span></h3>
                <p class="text-[12px] text-[var(--navy-light)] mb-4 leading-relaxed">
                    Ensure your upload file strictly matches the headers below:
                </p>
                <div class="font-mono text-[10px] text-navy bg-[var(--ivory)] p-3 border border-[var(--silver)] rounded-[2px] flex flex-col gap-1.5 overflow-x-auto select-all">
                    <span>year,ceremony,category,nominee,film,country,winner,source_url</span>
                </div>
                <div class="mt-4 flex flex-col gap-3 text-[11px] text-[var(--navy-light)]">
                    <p>• <strong class="text-navy">year</strong> & <strong class="text-navy">ceremony</strong>: Compound keys checked for duplicates.</p>
                    <p>• <strong class="text-navy">winner</strong>: Set to 1 (won) or 0 (nominated).</p>
                    <p>• Fields with commas are wrapped in quotes automatically if minimal quoting is used.</p>
                </div>
            </div>

        </div>

    </div>

</main>
<?php
require_once __DIR__ . '/../layouts/footer.php';
?>
