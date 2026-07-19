const http = require('http');

const urls = [
    'http://localhost:8000/',
    'http://localhost:8000/hollywood/american/oscars',
    'http://localhost:8000/hollywood/american/oscars/best-picture',
    'http://localhost:8000/persons/alia-bhatt',
    'http://localhost:8000/south-asian/lollywood/nigar-awards',
    'http://localhost:8000/search?q=alia',
    'http://localhost:8000/hollywood/american/oscars/2024'
];

async function checkUrl(url) {
    return new Promise((resolve) => {
        const req = http.get(url, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => {
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    console.log(`[OK] ${url} (HTTP ${res.statusCode})`);
                } else {
                    console.log(`[HTTP ERROR ${res.statusCode}] ${url}`);
                }
                
                if (data.includes('Ceremony Not Found') || data.includes('No records found') || data.includes('Archive Not Found') || data.includes('Profile Not Found')) {
                    console.log("  => Loaded fallback gracefully");
                }
                resolve();
            });
        });
        
        req.on('error', (e) => {
            console.log(`[CONNECTION ERROR] ${url}: ${e.message}`);
            resolve();
        });
    });
}

async function run() {
    for (const url of urls) {
        await checkUrl(url);
    }
}
run();
