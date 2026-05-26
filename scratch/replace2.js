const fs = require('fs');
const file = 'c:/Users/amank/Downloads/Office/DIFM-Extractor/frontend/src/app/page.tsx';
const lines = fs.readFileSync(file, 'utf8').split('\n');

lines.splice(1, 0, 'import MultiUpload from "../components/MultiUpload";');

let startIndex = -1;
let endIndex = -1;
let animateCount = 0;
for(let i = 1000; i < lines.length; i++) {
    if(lines[i].includes('<AnimatePresence mode="wait">')) {
        startIndex = i;
        break;
    }
}
for(let i = startIndex; i < lines.length; i++) {
    if(lines[i].includes('<AnimatePresence')) animateCount++;
    if(lines[i].includes('</AnimatePresence>')) {
        animateCount--;
        if(animateCount === 0) {
            endIndex = i;
            break;
        }
    }
}

if(startIndex !== -1 && endIndex !== -1) {
    lines.splice(startIndex, endIndex - startIndex + 1, '          <MultiUpload authUser={authUser} apiBase={apiBase} onSaveHistory={saveHistoryItem} />');
}

fs.writeFileSync(file, lines.join('\n'));
console.log('Successfully replaced MultiUpload component.');
