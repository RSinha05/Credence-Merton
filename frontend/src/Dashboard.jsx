import React, { useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, Search, Activity, BarChart3, Target, Shield, AlertTriangle, Home, DollarSign, Calculator, Layers } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { ASSET_UNIVERSE } from "./universe";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("multi-asset");

  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Retail State
  const [retailForm, setRetailForm] = useState({
    fico_score: 720, ltv: 80, dti: 35, loan_amount: 350000, interest_rate: 0.055, term_months: 360, months_seasoned: 12
  });
  const [retailResult, setRetailResult] = useState(null);
  const [retailLoading, setRetailLoading] = useState(false);

  const handleRetailChange = (e) => {
    setRetailForm({ ...retailForm, [e.target.name]: parseFloat(e.target.value) });
  };

  const analyzeRetail = async (e) => {
    e.preventDefault();
    setRetailLoading(true);
    setError(null);
    setRetailResult(null);
    try {
      const payload = { loans: [{ loan_id: "L-001", ...retailForm }] };
      const res = await axios.post(`http://127.0.0.1:8000/api/v1/risk/retail/portfolio`, payload);
      setRetailResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to analyze retail loan.");
    } finally {
      setRetailLoading(false);
    }
  };

  const [corporateTicker, setCorporateTicker] = useState("");
  const [corporateResult, setCorporateResult] = useState(null);
  const [corporateLoading, setCorporateLoading] = useState(false);

  const analyzeCorporate = async (e) => {
    e.preventDefault();
    if (!corporateTicker) return;
    setCorporateLoading(true);
    setError(null);
    setCorporateResult(null);
    try {
      const payload = { ticker: corporateTicker.toUpperCase(), time_horizon: 1.0, include_altman: true };
      const res = await axios.post(`http://127.0.0.1:8000/api/v1/risk/corporate/${corporateTicker.toUpperCase()}`, payload);
      setCorporateResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to analyze corporate asset.");
    } finally {
      setCorporateLoading(false);
    }
  };

  const renderCorporate = () => {
    if (!corporateResult) return (
      <div className="flex flex-col items-center justify-center h-full text-ivory/30 pt-20">
        <Activity size={48} className="mb-4 opacity-50" />
        <p className="text-xl font-serif">Enter a ticker to run the Ensemble Early Warning System.</p>
      </div>
    );

    const { merton, altman, ensemble } = corporateResult;
    return (
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <MetricCard title="Ensemble PD (1Y)" value={`${(ensemble.ensemble_pd * 100).toFixed(2)}%`} icon={<Target />} color="text-red-400" />
          <MetricCard title="Risk Tier" value={ensemble.risk_tier} icon={<Shield />} color={ensemble.risk_tier === "HIGH" ? "text-red-400" : "text-gold"} />
          <MetricCard title="Altman Z-Score" value={altman?.z_score?.toFixed(2) || "N/A"} icon={<Activity />} color={altman?.z_score < 1.8 ? "text-red-400" : "text-emerald-400"} />
          <MetricCard title="Z-Score Zone" value={altman?.z_zone || "N/A"} icon={<AlertTriangle />} />
        </div>
        <div className="p-6 bg-onyx-900/50 border border-white/5 text-sm text-ivory/70 leading-relaxed">
          <strong>Ensemble Agreement:</strong> {ensemble.models_agree ? "Yes" : "No"} <br/>
          <strong>Confidence Score:</strong> {(ensemble.confidence * 100).toFixed(1)}% <br/>
          <strong>Analysis:</strong> The ensemble model blends the structural Merton distance-to-default implied probability with the fundamental accounting-based Altman Z-Score probability proxy.
        </div>
      </motion.div>
    );
  };

  const analyzeTicker = async (e) => {
    e.preventDefault();
    if (!ticker) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await axios.get(`http://127.0.0.1:8000/api/v1/risk/multi-asset/${ticker.toUpperCase()}`);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to analyze asset. Please check the ticker symbol.");
    } finally {
      setLoading(false);
    }
  };

  const renderMultiAsset = () => {
    if (!result) return (
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
    );

    const { asset_type, metrics, risk_tier, ticker: t } = result;

    if (asset_type === "EQUITY") {
      return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <MetricCard title="Distance to Default (DD)" value={metrics.DD_rn?.toFixed(2)} icon={<Target />} color="text-emerald-400" />
            <MetricCard title="Prob. of Default (1Y)" value={`${(metrics.PD_rn * 100).toFixed(2)}%`} icon={<AlertTriangle />} color="text-red-400" />
            <MetricCard title="Asset Volatility" value={`${(metrics.sigma_V * 100).toFixed(2)}%`} icon={<Activity />} />
            <MetricCard title="FinBERT Sentiment" value={metrics.sentiment_score !== undefined ? metrics.sentiment_score.toFixed(2) : "N/A"} icon={<Activity />} color={metrics.sentiment_score < 0 ? "text-red-400" : "text-emerald-400"} />
          </div>
        </motion.div>
      );
    }

    if (asset_type === "ETF") {
      return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <MetricCard title="Risk Tier" value={risk_tier} icon={<Shield />} color={risk_tier === "HIGH" ? "text-red-400" : "text-gold"} />
            <MetricCard title="Max Drawdown" value={`${(result.max_drawdown * 100).toFixed(2)}%`} icon={<Activity />} />
            <MetricCard title="95% Daily VaR" value={`${(result.var_95_daily * 100).toFixed(2)}%`} icon={<AlertTriangle />} />
            <MetricCard title="Sharpe Ratio" value={result.sharpe_ratio.toFixed(2)} icon={<Target />} />
          </div>
        </motion.div>
      );
    }

    if (asset_type === "GOV_BOND") {
      return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <MetricCard title="Current Yield" value={`${(result.current_yield * 100).toFixed(2)}%`} icon={<Activity />} />
            <MetricCard title="Modified Duration" value={`${result.modified_duration.toFixed(2)} yrs`} icon={<BarChart3 />} />
            <MetricCard title="Convexity" value={result.convexity.toFixed(2)} icon={<Target />} />
            <MetricCard title="Rate Risk Tier" value={risk_tier} icon={<Shield />} color="text-gold" />
          </div>
        </motion.div>
      );
    }
  };

  const renderRetail = () => {
    return (
      <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col md:flex-row gap-12">
        <div className="w-full md:w-1/3">
          <h2 className="font-serif text-2xl mb-6 text-gold">Origination Inputs</h2>
          <form onSubmit={analyzeRetail} className="space-y-4">
            <div>
              <label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">FICO Score</label>
              <input type="number" name="fico_score" value={retailForm.fico_score} onChange={handleRetailChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" />
            </div>
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">LTV (%)</label>
                <input type="number" name="ltv" value={retailForm.ltv} onChange={handleRetailChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" />
              </div>
              <div className="flex-1">
                <label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">DTI (%)</label>
                <input type="number" name="dti" value={retailForm.dti} onChange={handleRetailChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" />
              </div>
            </div>
            <div>
              <label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">Loan Amount ($)</label>
              <input type="number" name="loan_amount" value={retailForm.loan_amount} onChange={handleRetailChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" />
            </div>
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">Rate (Dec)</label>
                <input type="number" step="0.001" name="interest_rate" value={retailForm.interest_rate} onChange={handleRetailChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" />
              </div>
              <div className="flex-1">
                <label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">Term (Mo)</label>
                <input type="number" name="term_months" value={retailForm.term_months} onChange={handleRetailChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" />
              </div>
            </div>
            <button type="submit" disabled={retailLoading} className="w-full bg-gold text-onyx-950 font-bold uppercase tracking-widest py-4 hover:bg-white transition-colors disabled:opacity-50 mt-4">
              {retailLoading ? "Training ML / Analyzing..." : "Run Credit Check"}
            </button>
          </form>
        </div>

        <div className="w-full md:w-2/3">
          {retailResult ? (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              <h2 className="font-serif text-2xl text-ivory/90 mb-6">Credit Origination Risk (XGBoost)</h2>
              <div className="grid grid-cols-2 gap-6">
                <MetricCard title="Expected Loss (EL)" value={`$${retailResult.portfolio_expected_loss.toLocaleString(undefined, {maximumFractionDigits:2})}`} icon={<DollarSign />} color="text-red-400" />
                <MetricCard title="Exposure at Default (EAD)" value={`$${retailResult.portfolio_total_ead.toLocaleString(undefined, {maximumFractionDigits:2})}`} icon={<Calculator />} />
                <MetricCard title="Prob. of Default (PD)" value={`${(retailResult.loan_results[0].pd * 100).toFixed(2)}%`} icon={<AlertTriangle />} color="text-red-400" />
                <MetricCard title="Loss Given Default (LGD)" value={`${(retailResult.loan_results[0].lgd * 100).toFixed(2)}%`} icon={<Layers />} color="text-gold" />
              </div>
              <div className="p-6 bg-onyx-900/50 border border-white/5 text-sm text-ivory/70 leading-relaxed">
                <strong>Analysis:</strong> The Expected Loss is mathematically derived as PD × LGD × EAD. The Probability of Default and Loss Given Default are inferred dynamically using an XGBoost Classifier and Regressor trained on synthetic historic mortgage tapes.
              </div>
            </motion.div>
          ) : (
             <div className="flex flex-col items-center justify-center h-full text-ivory/30 border border-white/5 bg-onyx-900/20 p-12">
               <Home size={48} className="mb-4 opacity-50" />
               <p className="text-xl font-serif text-center">Retail Mortgage Module</p>
               <p className="text-sm mt-2 text-center max-w-md">Input applicant credentials to calculate Expected Loss (EL) using our machine-learning derived credit models.</p>
             </div>
          )}
        </div>
      </motion.div>
    );
  };

  return (
    <div className="min-h-screen bg-onyx-950 text-ivory font-sans selection:bg-gold selection:text-onyx-950 flex flex-col">
      <nav className="border-b border-white/5 bg-onyx-950/80 backdrop-blur-md sticky top-0 z-50 p-6 flex justify-between items-center">
        <Link to="/" className="flex items-center gap-2 hover:text-gold transition-colors">
          <ChevronLeft size={20} />
          <span className="text-sm tracking-[0.2em] uppercase">Back to Hub</span>
        </Link>
        <div className="text-xl font-serif tracking-widest text-gold uppercase flex items-center gap-6">
          <button onClick={() => setActiveTab('multi-asset')} className={`transition-colors ${activeTab === 'multi-asset' ? 'text-gold' : 'text-ivory/30 hover:text-ivory/60'}`}>Multi-Asset & NLP</button>
          <span className="text-ivory/10">|</span>
          <button onClick={() => setActiveTab('corporate')} className={`transition-colors ${activeTab === 'corporate' ? 'text-gold' : 'text-ivory/30 hover:text-ivory/60'}`}>Corporate EWS</button>
          <span className="text-ivory/10">|</span>
          <button onClick={() => setActiveTab('retail')} className={`transition-colors ${activeTab === 'retail' ? 'text-gold' : 'text-ivory/30 hover:text-ivory/60'}`}>Retail Credit</button>
        </div>
      </nav>

      <main className="flex-1 max-w-7xl w-full mx-auto p-8 flex flex-col">
        <AnimatePresence mode="wait">
          <motion.div key={activeTab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
            {activeTab === 'multi-asset' && (
              <>
                <div className="mb-12">
                  <h1 className="text-5xl font-serif mb-4">Quantitative Risk Engine</h1>
                  <p className="text-ivory/50">Real-time asset modeling using Merton/KMV and FinBERT SEC Sentiment.</p>
                </div>

                <form onSubmit={analyzeTicker} className="relative max-w-xl mb-12">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-ivory/30">
                    <Search size={20} />
                  </div>
                  <input
                    type="text"
                    className="w-full bg-onyx-900 border border-white/10 rounded-none py-4 pl-12 pr-32 text-lg focus:outline-none focus:border-gold transition-colors text-ivory uppercase"
                    placeholder="E.G. AAPL, ^TNX, VOO"
                    value={ticker}
                    onChange={(e) => setTicker(e.target.value)}
                  />
                  <button
                    id="analyze-btn"
                    type="submit"
                    disabled={loading}
                    className="absolute inset-y-0 right-0 px-6 bg-gold text-onyx-950 font-bold uppercase tracking-widest text-sm hover:bg-white transition-colors disabled:opacity-50"
                  >
                    {loading ? "..." : "Analyze"}
                  </button>
                </form>

                {error && <div className="p-4 bg-red-900/20 border border-red-500/50 text-red-200 mb-8 max-w-xl">{error}</div>}
                
                <div className="flex-1">
                  {renderMultiAsset()}
                </div>
              </>
            )}

            {activeTab === 'retail' && (
              <>
                <div className="mb-12">
                  <h1 className="text-5xl font-serif mb-4">Retail Credit Check</h1>
                  <p className="text-ivory/50">Mortgage risk analysis using Expected Loss (EL) models.</p>
                </div>
                {error && <div className="p-4 bg-red-900/20 border border-red-500/50 text-red-200 mb-8 max-w-xl">{error}</div>}
                {renderRetail()}
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
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

function MetricCard({ title, value, icon, color = "text-gold" }) {
  return (
    <div className="bg-onyx-900/50 border border-white/5 p-6 relative overflow-hidden group hover:border-gold/30 transition-colors">
      <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity ${color}`}>
        {icon}
      </div>
      <div className="text-xs uppercase tracking-[0.2em] text-ivory/50 mb-4">{title}</div>
      <div className={`text-4xl font-light font-serif ${color}`}>{value || "—"}</div>
    </div>
  );
}
