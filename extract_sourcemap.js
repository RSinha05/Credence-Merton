const fs = require('fs');
const path = require('path');

async function extract() {
    console.log("Fetching source map...");
    const res = await fetch('https://prestige-finance-2.preview.emergentagent.com/static/js/bundle.js.map');
    const map = await res.json();
    
    console.log("Extracting files...");
    const sources = map.sources;
    const contents = map.sourcesContent;
    
    for (let i = 0; i < sources.length; i++) {
        let sourcePath = sources[i];
        
        if (!sourcePath.startsWith('/app/frontend/src/') || !contents[i]) {
            continue;
        }
        
        // Remove /app/frontend/
        const relativePath = sourcePath.replace('/app/frontend/', '');
        
        const fullPath = path.join(__dirname, 'frontend', relativePath);
        
        // Ensure directory exists
        const dir = path.dirname(fullPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        
        // Write file
        fs.writeFileSync(fullPath, contents[i]);
        console.log(`Extracted: ${relativePath}`);
    }
}
extract().catch(console.error);
