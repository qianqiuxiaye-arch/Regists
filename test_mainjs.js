const fs = require('fs');
const mainJs = fs.readFileSync('js/main.js', 'utf-8');
console.log('First 50 chars:', JSON.stringify(mainJs.slice(0, 50)));
const lines = mainJs.split('\n');
for(let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line.includes('`') && line.includes('<')) {
        console.log('Line ' + (i+1) + ' has < outside template:', line.trim().slice(0, 80));
    }
}
console.log('Total lines:', lines.length);
try {
    eval(fs.readFileSync('data/data.js', 'utf-8'));
    eval(mainJs);
    console.log('main.js eval OK');
} catch(e) {
    console.log('main.js eval ERROR:', e.message);
}
