const http = require('http');

http.get('http://localhost:8000/south-asian-cinema/bollywood/filmfare-awards/best-actress', (res) => {
    let data = '';
    res.on('data', (chunk) => { data += chunk; });
    res.on('end', () => {
        console.log(`STATUS: ${res.statusCode}`);
        if (data.includes('Ceremony Not Found')) console.log('Ceremony Not Found');
        else if (data.includes('Archive Not Found')) console.log('Archive Not Found');
        else console.log('Loaded successfully, Title:', data.match(/<title>(.*?)<\/title>/)[1]);
    });
});
