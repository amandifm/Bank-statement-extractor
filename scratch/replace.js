const fs = require('fs');
const file = 'c:/Users/amank/Downloads/Office/DIFM-Extractor/frontend/src/app/page.tsx';
let code = fs.readFileSync(file, 'utf8');

// Add import
code = code.replace('import Link from "next/link";', 'import Link from "next/link";\nimport MultiUpload from "../components/MultiUpload";');

// Remove single-file state
code = code.replace(/const \[file, setFile\][\s\S]*?const \[isTableExpanded, setIsTableExpanded\] = useState\(false\);/, '');

// Remove isImage
code = code.replace(/const isImage = useMemo[\s\S]*?\[file\]\);/, '');

// Remove handleFileChange through exportXlsx
code = code.replace(/async function handleFileChange[\s\S]*?function updateAuthField/m, 'function updateAuthField');

// Remove restoreHistoryItem logic
code = code.replace(/function restoreHistoryItem[\s\S]*?setIsTableExpanded\(false\);\s*\}/, 'function restoreHistoryItem(item: HistoryItem) {\n    // Multi-file queue doesn\'t support history restore yet\n  }');

// Remove auto-save useEffect
code = code.replace(/useEffect\(\(\) => \{\s*if \(status !== "complete"[\s\S]*?\}, \[status, file, authUser, savedHistoryKey\]\);/, '');

// Replace the UI block
code = code.replace(/<AnimatePresence mode="wait">\s*\{!file \? \([\s\S]*?<\/AnimatePresence>/, '<AnimatePresence mode="wait">\n          <MultiUpload authUser={authUser} apiBase={apiBase} onSaveHistory={saveHistoryItem} />\n        </AnimatePresence>');

// Remove logout state resets related to single file
code = code.replace(/setFile\(null\);\s*setVisibleRows\(\[\]\);\s*setProgress\(0\);\s*setStatus\("idle"\);\s*setShowScanner\(false\);\s*setIsTableExpanded\(false\);/g, '');

fs.writeFileSync(file, code);
console.log('Modified page.tsx');
