const fs = require('fs');

async function check() {
    const res = await fetch('https://prestige-finance-2.preview.emergentagent.com/static/js/bundle.js.map');
    const map = await res.json();
    console.log("Sources sample:", map.sources.filter(s => !s.includes('node_modules')).slice(0, 20));
}
check().catch(console.error);
