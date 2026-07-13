const fs = require('fs');
const dataJs = fs.readFileSync('data/data.js', 'utf-8');
const mainJs = fs.readFileSync('js/main.js', 'utf-8');

// Check file sizes
console.log('data.js size:', dataJs.length);
console.log('main.js size:', mainJs.length);

// Try to use the JS engine directly via require
try {
  // Write a temp module
  fs.writeFileSync('/tmp/__test_goglobal.js', 
    dataJs + '\n' + 
    'try {\n' + 
    mainJs + '\n' +
    '} catch(e) { console.log("ERR:", e.message); }\n'
  );
  const mod = require('/tmp/__test_goglobal.js');
  console.log('Module loaded OK');
  console.log('Regions:', GOGLOBAL_DATA.regions.regions.length);
} catch(e) {
  console.log('Module error:', e.message);
  // Show the line that failed
  const lines = e.stack.split('\n');
  console.log('Stack:', lines.slice(0, 3).join('\n'));
}
