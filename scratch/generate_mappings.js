const fs = require('fs');
const mysql = require('mysql2/promise');

async function run() {
    const navContent = fs.readFileSync('lib/navigation.php', 'utf-8');
    const match = navContent.match(/\$NAV_DATA_JSON\s*=\s*'(.*?)';/);
    const navData = JSON.parse(match[1]);
    
    const navSlugs = [];
    navData.forEach(region => {
        region.industries.forEach(ind => {
            ind.ceremonies.forEach(cer => {
                navSlugs.push({
                    navSlug: cer.slug,
                    name: cer.name,
                    country: cer.country
                });
            });
        });
    });

    const conn = await mysql.createConnection({
        host: '127.0.0.1',
        user: 'root',
        password: '',
        database: 'awardfilms_db'
    });

    const [dbCeremonies] = await conn.execute("SELECT id, name, slug FROM ceremonies");
    
    console.log("Mismatches found:");
    const map = {};
    for (const nav of navSlugs) {
        const exactMatch = dbCeremonies.find(db => db.slug === nav.navSlug);
        if (!exactMatch) {
            // Find fuzzy match
            const fuzzyMatch = dbCeremonies.find(db => {
                const dbName = db.name.toLowerCase();
                const navName = nav.name.toLowerCase();
                // Check if one contains the other
                if (dbName.includes(navName.replace(' (oscars)', '')) || navName.includes(dbName)) return true;
                
                // Compare words
                const dbWords = dbName.split(/\s+/).filter(w => w.length > 3);
                const navWords = navName.split(/\s+/).filter(w => w.length > 3);
                const common = dbWords.filter(w => navWords.includes(w));
                return common.length >= 1;
            });
            
            if (fuzzyMatch) {
                console.log(`- '${nav.navSlug}' => '${fuzzyMatch.slug}', // UI: ${nav.name} | DB: ${fuzzyMatch.name}`);
                map[nav.navSlug] = fuzzyMatch.slug;
            } else {
                console.log(`- MISSING IN DB: ${nav.navSlug} (${nav.name})`);
            }
        }
    }
    
    console.log("\nSuggested SlugMap additions:");
    for (const k in map) {
        console.log(`        '${k}' => '${map[k]}',`);
    }

    conn.end();
}
run();
