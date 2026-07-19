const http = require('http');

http.get('http://localhost:8000/western-european-cinema/hollywood/oscars/best-picture', (res) => {
    let data = '';
    res.on('data', (chunk) => { data += chunk; });
    res.on('end', () => {
        console.log(`STATUS: ${res.statusCode}`);
        console.log("Response:", data.substring(0, 500));
    });
});
