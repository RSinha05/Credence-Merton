import React, { useState } from 'react';

function App() {
  const [ticker, setTicker] = useState('AAPL');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      // Pointing to our FastAPI backend
      const res = await fetch(`http://127.0.0.1:8000/api/v1/risk/multi-asset/${ticker}`);
      if (!res.ok) throw new Error('API Error');
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      alert('Failed to fetch data. Ensure FastAPI is running.');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-dark text-white font-sans selection:bg-gold selection:text-dark">
      {/* Navbar */}
      <nav className="border-b border-white/10 p-6 flex justify-between items-center">
        <div className="text-2xl font-serif tracking-widest text-gold uppercase">Aurelis</div>
        <div className="space-x-8 text-sm tracking-widest text-white/60">
          <a href="#showcase" className="hover:text-gold transition-colors">PLATFORM</a>
          <a href="#methodology" className="hover:text-gold transition-colors">METHODOLOGY</a>
          <a href="#contact" className="hover:text-gold transition-colors">INSTITUTIONAL ACCESS</a>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="max-w-6xl mx-auto px-6 py-32 text-center">
        <h1 className="text-7xl font-serif mb-6 leading-tight">
          The Gold Standard in <br />
          <span className="text-gold italic">Credit Intelligence.</span>
        </h1>
        <p className="text-xl text-white/60 max-w-2xl mx-auto font-light leading-relaxed mb-12">
          Harness the power of Merton/KMV distance-to-default analytics, dynamic DTW clustering, and multi-asset risk scoring tailored for private banks and tier-1 institutions.
        </p>
        <button className="bg-gold text-dark px-8 py-4 uppercase tracking-widest text-sm font-semibold hover:bg-white transition-all duration-300">
          Request Access
        </button>
      </header>

      {/* Showcase API Section */}
      <section id="showcase" className="bg-surface py-24 border-y border-white/5">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl font-serif mb-4">Real-Time Risk Engine</h2>
          <p className="text-white/50 mb-12">Analyze global equities, sovereign bonds, and high-yield ETFs instantly.</p>
          
          <div className="flex justify-center max-w-lg mx-auto mb-12 relative">
            <input 
              type="text" 
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="Enter Ticker (e.g., AAPL, ^TNX, RELIANCE.NS)"
              className="w-full bg-dark border border-white/20 text-white px-6 py-4 outline-none focus:border-gold transition-colors tracking-widest"
            />
            <button 
              onClick={handleAnalyze}
              disabled={loading}
              className="absolute right-0 top-0 bottom-0 bg-gold text-dark px-6 font-semibold uppercase tracking-widest hover:bg-white transition-colors"
            >
              {loading ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>

          {result && (
            <div className="text-left bg-dark border border-white/10 p-8">
              <h3 className="text-2xl font-serif text-gold mb-6 border-b border-white/10 pb-4">
                Analysis Results: {result.ticker} ({result.asset_type})
              </h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                {result.asset_type === 'EQUITY' && result.metrics && (
                  <>
                    <div>
                      <div className="text-xs text-white/40 uppercase tracking-widest mb-1">Dist. to Default</div>
                      <div className="text-2xl font-light">{result.metrics.DD_rn?.toFixed(2) || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-xs text-white/40 uppercase tracking-widest mb-1">Prob. of Default</div>
                      <div className="text-2xl font-light text-red-400">{(result.metrics.PD_rn * 100)?.toFixed(2)}%</div>
                    </div>
                    <div>
                      <div className="text-xs text-white/40 uppercase tracking-widest mb-1">Asset Volatility</div>
                      <div className="text-2xl font-light">{(result.metrics.sigma_V * 100)?.toFixed(2)}%</div>
                    </div>
                    <div>
                      <div className="text-xs text-white/40 uppercase tracking-widest mb-1">Market Cap</div>
                      <div className="text-2xl font-light">${(result.metrics.V_current / 1e9)?.toFixed(1)}B</div>
                    </div>
                  </>
                )}
                
                {result.asset_type === 'ETF' && (
                  <>
                    <div>
                      <div className="text-xs text-white/40 uppercase tracking-widest mb-1">Risk Tier</div>
                      <div className={`text-2xl font-light ${result.risk_tier === 'HIGH' ? 'text-red-400' : 'text-green-400'}`}>{result.risk_tier}</div>
                    </div>
                    <div>
                      <div className="text-xs text-white/40 uppercase tracking-widest mb-1">Max Drawdown</div>
                      <div className="text-2xl font-light">{(result.max_drawdown * 100).toFixed(2)}%</div>
                    </div>
                    <div>
                      <div className="text-xs text-white/40 uppercase tracking-widest mb-1">95% Daily VaR</div>
                      <div className="text-2xl font-light">{(result.var_95_daily * 100).toFixed(2)}%</div>
                    </div>
                    <div>
                      <div className="text-xs text-white/40 uppercase tracking-widest mb-1">Sharpe Ratio</div>
                      <div className="text-2xl font-light">{result.sharpe_ratio.toFixed(2)}</div>
                    </div>
                  </>
                )}
                
                {result.asset_type === 'GOV_BOND' && (
                  <>
                    <div>
                      <div className="text-xs text-white/40 uppercase tracking-widest mb-1">Current Yield</div>
                      <div className="text-2xl font-light">{(result.current_yield * 100).toFixed(2)}%</div>
                    </div>
                    <div>
                      <div className="text-xs text-white/40 uppercase tracking-widest mb-1">Modified Duration</div>
                      <div className="text-2xl font-light">{result.modified_duration.toFixed(2)} yrs</div>
                    </div>
                    <div>
                      <div className="text-xs text-white/40 uppercase tracking-widest mb-1">Convexity</div>
                      <div className="text-2xl font-light">{result.convexity.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-white/40 uppercase tracking-widest mb-1">Rate Risk Tier</div>
                      <div className="text-2xl font-light text-gold">{result.risk_tier}</div>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="text-center py-12 text-white/30 text-sm tracking-widest border-t border-white/5">
        &copy; 2026 AURELIS INTELLIGENCE. ALL RIGHTS RESERVED.
      </footer>
    </div>
  );
}

export default App;
