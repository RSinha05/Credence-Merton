import re

with open('frontend/src/Dashboard.jsx', 'r') as f:
    content = f.read()

corporate_empty_state = """    if (!corporateResult) return (
      <div className="flex flex-col items-center justify-center h-full text-ivory/30 pt-20">
        <Activity size={48} className="mb-4 opacity-50" />
        <p className="text-xl font-serif">Enter a ticker to run the Ensemble Early Warning System.</p>
      </div>
    );"""

new_corporate_empty = """    if (!corporateResult) return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-8">
        <div className="flex flex-col items-center justify-center text-ivory/30 pb-10">
          <Activity size={48} className="mb-4 opacity-50" />
          <p className="text-xl font-serif">Enter a ticker to run the Ensemble Early Warning System.</p>
        </div>
        <h3 className="text-sm font-bold uppercase tracking-widest text-gold mb-6 border-b border-white/5 pb-4">Curated Global Equities</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {ASSET_UNIVERSE.filter(a => a.type === 'EQUITY').map((asset) => (
            <button 
              key={asset.ticker}
              onClick={() => {
                setCorporateTicker(asset.ticker);
                setTimeout(() => {
                  document.getElementById("corp-analyze-btn").click();
                }, 50);
              }}
              className="text-left p-4 bg-onyx-900/40 border border-white/5 hover:border-gold/30 hover:bg-onyx-900 transition-all group"
            >
              <div className="flex justify-between items-center mb-2">
                <span className="font-mono text-sm text-ivory group-hover:text-gold transition-colors">{asset.ticker}</span>
                <span className="text-[10px] uppercase tracking-widest text-ivory/40 bg-onyx-950 px-2 py-1 rounded-sm">EQ</span>
              </div>
              <div className="text-xs text-ivory/50 truncate">{asset.name}</div>
            </button>
          ))}
        </div>
      </motion.div>
    );"""

content = content.replace(corporate_empty_state, new_corporate_empty)

# Update corporate submit button to have id
corp_btn = """                  <button
                    type="submit"
                    disabled={corporateLoading}
                    className="absolute inset-y-0 right-0 px-6 bg-gold text-onyx-950 font-bold uppercase tracking-widest text-sm hover:bg-white transition-colors disabled:opacity-50\"
                  >
                    {corporateLoading ? "..." : "Analyze"}
                  </button>"""

new_corp_btn = """                  <button
                    id="corp-analyze-btn"
                    type="submit"
                    disabled={corporateLoading}
                    className="absolute inset-y-0 right-0 px-6 bg-gold text-onyx-950 font-bold uppercase tracking-widest text-sm hover:bg-white transition-colors disabled:opacity-50\"
                  >
                    {corporateLoading ? "..." : "Analyze"}
                  </button>"""
                  
content = content.replace(corp_btn, new_corp_btn)

with open('frontend/src/Dashboard.jsx', 'w') as f:
    f.write(content)
