with open('frontend/src/Dashboard.jsx', 'r') as f:
    content = f.read()

# Add new tab in nav
old_nav = """          <button onClick={() => setActiveTab('multi-asset')} className={`transition-colors ${activeTab === 'multi-asset' ? 'text-gold' : 'text-ivory/30 hover:text-ivory/60'}`}>Multi-Asset Engine</button>
          <span className="text-ivory/10">|</span>
          <button onClick={() => setActiveTab('retail')} className={`transition-colors ${activeTab === 'retail' ? 'text-gold' : 'text-ivory/30 hover:text-ivory/60'}`}>Retail Credit</button>"""

new_nav = """          <button onClick={() => setActiveTab('multi-asset')} className={`transition-colors ${activeTab === 'multi-asset' ? 'text-gold' : 'text-ivory/30 hover:text-ivory/60'}`}>Multi-Asset & NLP</button>
          <span className="text-ivory/10">|</span>
          <button onClick={() => setActiveTab('corporate')} className={`transition-colors ${activeTab === 'corporate' ? 'text-gold' : 'text-ivory/30 hover:text-ivory/60'}`}>Corporate EWS</button>
          <span className="text-ivory/10">|</span>
          <button onClick={() => setActiveTab('retail')} className={`transition-colors ${activeTab === 'retail' ? 'text-gold' : 'text-ivory/30 hover:text-ivory/60'}`}>Retail Credit</button>"""
content = content.replace(old_nav, new_nav)

# Replace the closing of activeTab === 'retail' with the new Corporate EWS section
old_retail_close = """                {renderRetail()}
              </>
            )}
          </motion.div>"""

new_corporate_tab = """                {renderRetail()}
              </>
            )}

            {activeTab === 'corporate' && (
              <>
                <div className="mb-12">
                  <h1 className="text-5xl font-serif mb-4">Corporate EWS</h1>
                  <p className="text-ivory/50">Early Warning System using Ensemble (Merton + Altman Z-Score) for deep corporate distress analysis.</p>
                </div>

                <form onSubmit={analyzeCorporate} className="relative max-w-xl mb-12">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-ivory/30">
                    <Search size={20} />
                  </div>
                  <input
                    type="text"
                    className="w-full bg-onyx-900 border border-white/10 rounded-none py-4 pl-12 pr-32 text-lg focus:outline-none focus:border-gold transition-colors text-ivory uppercase"
                    placeholder="E.G. TSLA, NVDA"
                    value={corporateTicker}
                    onChange={(e) => setCorporateTicker(e.target.value)}
                  />
                  <button
                    type="submit"
                    disabled={corporateLoading}
                    className="absolute inset-y-0 right-0 px-6 bg-gold text-onyx-950 font-bold uppercase tracking-widest text-sm hover:bg-white transition-colors disabled:opacity-50"
                  >
                    {corporateLoading ? "..." : "Analyze"}
                  </button>
                </form>

                {error && <div className="p-4 bg-red-900/20 border border-red-500/50 text-red-200 mb-8 max-w-xl">{error}</div>}
                
                <div className="flex-1">
                  {renderCorporate()}
                </div>
              </>
            )}
          </motion.div>"""
content = content.replace(old_retail_close, new_corporate_tab)

with open('frontend/src/Dashboard.jsx', 'w') as f:
    f.write(content)
