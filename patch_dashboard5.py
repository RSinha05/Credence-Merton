import re

with open('frontend/src/Dashboard.jsx', 'r') as f:
    content = f.read()

import_inject = """import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { ASSET_UNIVERSE } from "./universe";"""

content = content.replace('import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";', import_inject)

# In multi-asset, replace the empty state with the Curated Universe grid
empty_state = """    if (!result) return (
      <div className="flex flex-col items-center justify-center h-full text-ivory/30 pt-20">
        <Activity size={48} className="mb-4 opacity-50" />
        <p className="text-xl font-serif">Enter a ticker to begin quantitative analysis.</p>
        <p className="text-sm mt-2">Supports Global Equities, Sovereign Bonds, and ETFs.</p>
      </div>
    );"""

new_empty_state = """    if (!result) return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-8">
        <h3 className="text-sm font-bold uppercase tracking-widest text-gold mb-6 border-b border-white/5 pb-4">Curated Global Universe</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {ASSET_UNIVERSE.map((asset) => (
            <button 
              key={asset.ticker}
              onClick={() => {
                setTicker(asset.ticker);
                // Trigger form submit equivalent
                setTimeout(() => {
                  document.getElementById("analyze-btn").click();
                }, 50);
              }}
              className="text-left p-4 bg-onyx-900/40 border border-white/5 hover:border-gold/30 hover:bg-onyx-900 transition-all group"
            >
              <div className="flex justify-between items-center mb-2">
                <span className="font-mono text-sm text-ivory group-hover:text-gold transition-colors">{asset.ticker}</span>
                <span className="text-[10px] uppercase tracking-widest text-ivory/40 bg-onyx-950 px-2 py-1 rounded-sm">{asset.type === 'EQUITY' ? 'EQ' : asset.type === 'GOV_BOND' ? 'BOND' : 'ETF'}</span>
              </div>
              <div className="text-xs text-ivory/50 truncate">{asset.name}</div>
            </button>
          ))}
        </div>
      </motion.div>
    );"""

content = content.replace(empty_state, new_empty_state)

# Add an id to the analyze button so we can programmatically click it
button_old = """                  <button
                    type="submit"
                    disabled={loading}"""
button_new = """                  <button
                    id="analyze-btn"
                    type="submit"
                    disabled={loading}"""

content = content.replace(button_old, button_new)

with open('frontend/src/Dashboard.jsx', 'w') as f:
    f.write(content)
