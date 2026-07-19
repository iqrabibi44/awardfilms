<?php
session_start();
define('ADMIN_PASSWORD', 'admin-awardfilms-2026');
define('ADMIN_USERNAME', 'admin');

// Authentication check
$is_logged_in = isset($_SESSION['admin_logged_in']) && $_SESSION['admin_logged_in'] === true;
if (!$is_logged_in) {
    header('Location: index.php');
    exit;
}

$import_stats = null;
$import_error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['csv_file'])) {
    try {
        require_once __DIR__ . '/../lib/csv_importer.php';
        
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

$pageTitle = "Upload CSV - Admin";
require_once __DIR__ . '/../layouts/head.php';
require_once __DIR__ . '/../layouts/header.php';
?>
<main class="mx-auto w-full max-w-[1200px] px-6 py-12">
    <div class="flex items-center justify-between mb-8 pb-6 border-b border-[var(--silver)]">
        <div>
            <h1 class="text-3xl font-serif font-bold text-navy">CSV <span class="gold-italic">Upload</span></h1>
        </div>
        <a href="index.php" class="text-xs font-bold uppercase tracking-wider text-[var(--navy-light)] hover:text-[var(--gold)]">&larr; Back to Dashboard</a>
    </div>

    <div class="bg-white border border-[var(--glass-border)] rounded shadow p-8 max-w-3xl mx-auto">
        <h2 class="text-xl font-serif font-bold text-navy mb-4">Import Scraped Data</h2>
        <p class="text-sm text-[var(--navy-light)] mb-6">
            Upload your CSV file below. The system automatically filters out duplicates using native `INSERT IGNORE` and `ON DUPLICATE KEY UPDATE` rules matching Category, Edition, Nominee, and Film. Commas inside values are safely handled.
        </p>

        <?php if ($import_error): ?>
            <div class="mb-6 bg-red-50 border-s-4 border-red-500 text-red-700 p-4 text-[12px] rounded" role="alert">
                <p class="font-bold mb-1">Import Failed</p>
                <p><?php echo htmlspecialchars($import_error); ?></p>
            </div>
        <?php endif; ?>

        <?php if ($import_stats): ?>
            <div class="mb-6 bg-green-50 border-s-4 border-green-500 text-green-800 p-5 text-[13px] rounded">
                <h3 class="font-bold text-sm mb-3">✓ Import Completed Successfully!</h3>
                <ul class="list-disc ms-5 space-y-1">
                    <li>Rows Processed: <?php echo $import_stats['total_rows']; ?></li>
                    <li>Skipped: <?php echo $import_stats['skipped_rows']; ?></li>
                    <li>New Ceremonies: <?php echo $import_stats['ceremonies_created']; ?></li>
                    <li>New Categories: <?php echo $import_stats['categories_created']; ?></li>
                    <li>New Nominations Inserted: <?php echo $import_stats['nominations_inserted']; ?></li>
                    <li>Duplicates Updated: <?php echo $import_stats['nominations_updated']; ?></li>
                </ul>
            </div>
        <?php endif; ?>

        <form action="upload.php" method="POST" enctype="multipart/form-data" class="flex flex-col gap-6">
            <div class="border-2 border-dashed border-[var(--silver)] hover:border-[var(--gold)] bg-[var(--ivory)] hover:bg-[var(--ivory-deep)] rounded-[4px] px-8 py-12 text-center relative cursor-pointer transition-all duration-300">
                <input type="file" name="csv_file" accept=".csv" required class="absolute inset-0 w-full h-full opacity-0 cursor-pointer">
                <div class="text-navy font-bold text-lg mb-2">Click to Browse or Drop CSV File Here</div>
                <div class="text-[var(--navy-light)] text-xs uppercase tracking-wider">Format: year, ceremony, category, nominee, film, country, winner, source_url</div>
            </div>
            <button type="submit" class="bg-navy text-white text-xs font-bold uppercase tracking-wider py-3.5 px-7 rounded-[3px] hover:bg-[var(--gold)] transition-all duration-300 self-start shadow-sm hover:shadow">
                Secure Upload & Merge
            </button>
        </form>
    </div>
</main>
<?php require_once __DIR__ . '/../layouts/footer.php'; ?>
