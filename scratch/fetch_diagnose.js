const http = require('http');

http.get('http://localhost:8000/scratch/diagnose.php', (res) => {
    let data = '';
    res.on('data', (chunk) => { data += chunk; });
    res.on('end', () => {
        console.log(data);
    });
});
