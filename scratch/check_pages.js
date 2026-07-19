const http = require('http');

const urls = [
    'http://localhost:8000/',
    'http://localhost:8000/search?q=alia',
    'http://localhost:8000/hollywood/american/oscars',
    'http://localhost:8000/hollywood/american/oscars/2024',
    'http://localhost:8000/persons/alia-bhatt'
];

async function checkUrl(url) {
    return new Promise((resolve) => {
        const req = http.get(url, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => {
                if (data.includes('Fatal error') || data.includes('Parse error')) {
                    console.log(`[ERROR] Found PHP error in ${url}`);
                    console.log(data.substring(0, 500));
                } else {
                    console.log(`[OK] ${url} (HTTP ${res.statusCode})`);
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
