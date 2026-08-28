import React, { useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";

axios.defaults.auth = {
  username: "credence",
  password: "mertonx_api_secret"
};

import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, Search, Activity, BarChart3, Target, Shield, AlertTriangle, Home, DollarSign, Calculator, Layers, TrendingDown, Building2, Briefcase, Landmark, Zap } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, Cell } from "recharts";
import { ASSET_UNIVERSE } from "./universe";
import { PE_UNIVERSE } from "./pe_universe";

const combinedMap = new Map();
ASSET_UNIVERSE.forEach(a => combinedMap.set(a.ticker, a));
PE_UNIVERSE.forEach(a => {
  if (!combinedMap.has(a.ticker)) {
    combinedMap.set(a.ticker, { ...a, type: 'EQUITY' });
  }
});
const sortedAssets = Array.from(combinedMap.values()).sort((a, b) => a.name.localeCompare(b.name));
const sortedPe = [...PE_UNIVERSE].sort((a, b) => a.name.localeCompare(b.name));
const sortedRetail = [
  "APP-1092 (John Doe)", "APP-2044 (Jane Smith)", "APP-3091 (Robert Chen)", 
  "APP-4011 (Maria Garcia)", "LOAN-8821 (Refinance)", "LOAN-9923 (Purchase)"
].sort();


const API = "http://127.0.0.1:8000";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("multi-asset");
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Retail State
  const [retailSearch, setRetailSearch] = useState("");
  const handleRetailSearch = (e) => {
    e.preventDefault();
    if (!retailSearch) return;
    setRetailForm({
      fico_score: 650 + Math.floor(Math.random() * 100),
      ltv: 70 + Math.floor(Math.random() * 20),
      dti: 25 + Math.floor(Math.random() * 15),
      loan_amount: 250000 + Math.floor(Math.random() * 300000),
      interest_rate: 0.045 + (Math.random() * 0.03),
      term_months: 360, months_seasoned: 12
    });
    setTimeout(() => { const btn = document.getElementById("retail-btn"); if(btn) btn.click(); }, 300);
  };

  // Private Equity Search State
  const [peSearch, setPeSearch] = useState("");
  const handlePeSearch = (e) => {
    e.preventDefault();
    if (!peSearch) return;
    setPeForm({
      name: peSearch.toUpperCase(),
      sector: ["Tech", "Healthcare", "Consumer", "Financials"][Math.floor(Math.random()*4)],
      geography: "US",
      ebitda: 50 + Math.floor(Math.random() * 400),
      total_debt: 200 + Math.floor(Math.random() * 1000),
      equity_book_value: 100 + Math.floor(Math.random() * 500),
      revenue: 300 + Math.floor(Math.random() * 1500)
    });
    setTimeout(() => { const btn = document.getElementById("pe-btn"); if(btn) btn.click(); }, 300);
  };
  const [retailForm, setRetailForm] = useState({
    fico_score: 720, ltv: 80, dti: 35, loan_amount: 350000, interest_rate: 0.055, term_months: 360, months_seasoned: 12
  });
  const [retailResult, setRetailResult] = useState(null);
  const [retailLoading, setRetailLoading] = useState(false);
  const handleRetailChange = (e) => {
    setRetailForm({ ...retailForm, [e.target.name]: parseFloat(e.target.value) });
  };
  const analyzeRetail = async (e) => {
    e.preventDefault(); setRetailLoading(true); setError(null); setRetailResult(null);
    try {
      const payload = { loans: [{ loan_id: "L-001", ...retailForm }] };
      const res = await axios.post(`${API}/api/v1/risk/retail/portfolio`, payload);
      setRetailResult(res.data);
    } catch (err) { setError(err.response?.data?.detail || "Failed to analyze retail loan."); }
    finally { setRetailLoading(false); }
  };

  // Corporate State
  const [corporateTicker, setCorporateTicker] = useState("");
  const [corporateResult, setCorporateResult] = useState(null);
  const [corporateLoading, setCorporateLoading] = useState(false);
  const [deepResult, setDeepResult] = useState(null);

  const analyzeCorporate = async (e) => {
    e.preventDefault();
    if (!corporateTicker) return;
    setCorporateLoading(true); setError(null); setCorporateResult(null); setDeepResult(null);
    try {
      const payload = { ticker: corporateTicker.toUpperCase(), time_horizon: 1.0, include_altman: true };
      const [corpRes, deepRes] = await Promise.all([
        axios.post(`${API}/api/v1/risk/corporate/${corporateTicker.toUpperCase()}`, payload),
        axios.get(`${API}/api/v1/analytics/deep/${corporateTicker.toUpperCase()}`).catch(() => null)
      ]);
      setCorporateResult(corpRes.data);
      if (deepRes) setDeepResult(deepRes.data);
    } catch (err) { setError(err.response?.data?.detail || "Failed to analyze corporate asset."); }
    finally { setCorporateLoading(false); }
  };

  // Stress Testing State
  const [stressTicker, setStressTicker] = useState("");
  const [stressResult, setStressResult] = useState(null);
  const [stressLoading, setStressLoading] = useState(false);
  const analyzeStress = async (e) => {
    e.preventDefault();
    if (!stressTicker) return;
    setStressLoading(true); setError(null); setStressResult(null);
    try {
      const res = await axios.get(`${API}/api/v1/analytics/stress/${stressTicker.toUpperCase()}`);
      setStressResult(res.data);
    } catch (err) { setError(err.response?.data?.detail || "Failed to run stress test."); }
    finally { setStressLoading(false); }
  };

  // Private Equity State
  const [peForm, setPeForm] = useState({
    name: "PortCo Alpha", sector: "Tech", geography: "US",
    ebitda: 150, total_debt: 500, equity_book_value: 200, revenue: 800
  });
  const [peResult, setPeResult] = useState(null);
  const [peLoading, setPeLoading] = useState(false);
  const [lboResult, setLboResult] = useState(null);
  const handlePeChange = (e) => {
    const val = ["ebitda","total_debt","equity_book_value","revenue"].includes(e.target.name)
      ? parseFloat(e.target.value) : e.target.value;
    setPeForm({ ...peForm, [e.target.name]: val });
  };
  const analyzePE = async (e) => {
    e.preventDefault(); setPeLoading(true); setError(null); setPeResult(null);
    try {
      const res = await axios.post(`${API}/api/v1/risk/private/company`, peForm);
      setPeResult(res.data);
    } catch (err) { setError(err.response?.data?.detail || "Failed to analyze private company."); }
    finally { setPeLoading(false); }
  };
  const loadSampleLBO = async () => {
    try { const res = await axios.get(`${API}/api/v1/risk/private/lbo/sample`); setLboResult(res.data); }
    catch (err) { setError("Failed to load sample LBO."); }
  };

  // Multi-Asset handler
  const analyzeTicker = async (e) => {
    e.preventDefault();
    if (!ticker) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await axios.get(`${API}/api/v1/risk/multi-asset/${ticker.toUpperCase()}`);
      setResult(res.data);
    } catch (err) { setError(err.response?.data?.detail || "Failed to analyze asset."); }
    finally { setLoading(false); }
  };

  // === RENDER: MULTI-ASSET ===
  const renderMultiAsset = () => {
    if (!result) return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-8">
        <h3 className="text-sm font-bold uppercase tracking-widest text-gold mb-6 border-b border-white/5 pb-4">Curated Global Universe</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {ASSET_UNIVERSE.map((asset) => (
            <button key={asset.ticker} onClick={() => { setTicker(asset.ticker); setTimeout(() => document.getElementById("analyze-btn").click(), 50); }}
              className="text-left p-4 bg-onyx-900/40 border border-white/5 hover:border-gold/30 hover:bg-onyx-900 transition-all group">
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
    const { asset_type, metrics, risk_tier } = result;
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

  // === RENDER: CORPORATE EWS (enhanced with Phase 2 deep analytics) ===
  const renderCorporate = () => {
    if (!corporateResult) return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-8">
        <div className="flex flex-col items-center justify-center text-ivory/30 pb-10">
          <Activity size={48} className="mb-4 opacity-50" />
          <p className="text-xl font-serif">Enter a ticker to run the Ensemble Early Warning System.</p>
        </div>
        <h3 className="text-sm font-bold uppercase tracking-widest text-gold mb-6 border-b border-white/5 pb-4">Curated Global Equities</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {ASSET_UNIVERSE.filter(a => a.type === 'EQUITY').map((asset) => (
            <button key={asset.ticker} onClick={() => { setCorporateTicker(asset.ticker); setTimeout(() => document.getElementById("corp-analyze-btn").click(), 50); }}
              className="text-left p-4 bg-onyx-900/40 border border-white/5 hover:border-gold/30 hover:bg-onyx-900 transition-all group">
              <div className="flex justify-between items-center mb-2">
                <span className="font-mono text-sm text-ivory group-hover:text-gold transition-colors">{asset.ticker}</span>
                <span className="text-[10px] uppercase tracking-widest text-ivory/40 bg-onyx-950 px-2 py-1 rounded-sm">EQ</span>
              </div>
              <div className="text-xs text-ivory/50 truncate">{asset.name}</div>
            </button>
          ))}
        </div>
      </motion.div>
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

        {/* Phase 2: Bank-Grade Analytics Panel */}
        {deepResult && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <h3 className="text-sm font-bold uppercase tracking-widest text-gold border-b border-white/5 pb-4">Bank-Grade Analytics</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <MetricCard title="Implied Rating" value={deepResult.implied_rating} icon={<Landmark />} color="text-gold" />
              <MetricCard title="Basel IRB Capital (K)" value={`${((deepResult.regulatory_capital?.K || 0) * 100).toFixed(2)}%`} icon={<Shield />} color="text-amber-400" />
              <MetricCard title="RWA Density" value={`${((deepResult.regulatory_capital?.RWA_density || 0) * 100).toFixed(1)}%`} icon={<BarChart3 />} />
              <MetricCard title="Asset Correlation" value={`${((deepResult.regulatory_capital?.rho || 0) * 100).toFixed(1)}%`} icon={<Activity />} />
            </div>
            {deepResult.ttc_pit && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <MetricCard title="TTC PD" value={`${((deepResult.ttc_pit.ttc?.pd || 0) * 100).toFixed(3)}%`} icon={<Target />} color="text-blue-400" />
                <MetricCard title="TTC Rating" value={deepResult.ttc_pit.ttc?.rating || "N/A"} icon={<Shield />} color="text-blue-400" />
                <MetricCard title="PIT / TTC Ratio" value={deepResult.ttc_pit.ratio?.toFixed(2) || "N/A"} icon={<TrendingDown />} color={deepResult.ttc_pit.ratio > 1.5 ? "text-red-400" : "text-emerald-400"} />
              </div>
            )}
            {deepResult.cecl && (
              <div className="p-6 bg-onyx-900/50 border border-white/5">
                <h4 className="text-xs uppercase tracking-widest text-gold mb-4">CECL Lifetime Expected Loss</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <div className="text-xs text-ivory/50 mb-1">Weighted Lifetime PD</div>
                    <div className="text-2xl font-serif text-red-400">{((deepResult.cecl.weighted_lifetime_pd || 0) * 100).toFixed(2)}%</div>
                  </div>
                  <div>
                    <div className="text-xs text-ivory/50 mb-1">CECL Expected Loss (per $1)</div>
                    <div className="text-2xl font-serif text-gold">{((deepResult.cecl.cecl_expected_loss || 0) * 100).toFixed(3)}%</div>
                  </div>
                  <div>
                    <div className="text-xs text-ivory/50 mb-1">Scenario Breakdown</div>
                    {deepResult.cecl.scenario_results && Object.entries(deepResult.cecl.scenario_results).map(([name, sc]) => (
                      <div key={name} className="flex justify-between text-xs text-ivory/60 py-1 border-b border-white/5">
                        <span className="capitalize">{name}</span>
                        <span className="font-mono">{((sc.lifetime_pd || 0) * 100).toFixed(2)}% (wt: {((sc.weight || 0) * 100).toFixed(0)}%)</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}

        <div className="p-6 bg-onyx-900/50 border border-white/5 text-sm text-ivory/70 leading-relaxed">
          <strong>Ensemble Agreement:</strong> {ensemble.models_agree ? "Yes" : "No"} <br/>
          <strong>Confidence Score:</strong> {(ensemble.confidence * 100).toFixed(1)}% <br/>
          <strong>Analysis:</strong> The ensemble model blends the structural Merton distance-to-default implied probability with the fundamental accounting-based Altman Z-Score probability proxy.
        </div>
      </motion.div>
    );
  };

  // === RENDER: RETAIL ===
  const renderRetail = () => (
    <>
      <form onSubmit={handleRetailSearch} className="relative max-w-xl mb-12">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-ivory/30"><Search size={20} /></div>
        <input type="text" list="retail-list" className="w-full bg-onyx-900 border border-white/10 rounded-none py-4 pl-12 pr-32 text-lg focus:outline-none focus:border-gold transition-colors text-ivory uppercase"
          placeholder="SEARCH LOAN ID OR APPLICANT..." value={retailSearch} onChange={(e) => setRetailSearch(e.target.value)} />
        <datalist id="retail-list">{sortedRetail.map(r => <option key={r} value={r.split(" ")[0]}>{r}</option>)}</datalist>
        <button type="submit" className="absolute inset-y-0 right-0 px-6 bg-gold text-onyx-950 font-bold uppercase tracking-widest text-sm hover:bg-white transition-colors">
          Search</button>
      </form>
    <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col md:flex-row gap-12">
      <div className="w-full md:w-1/3">
        <h2 className="font-serif text-2xl mb-6 text-gold">Origination Inputs</h2>
        <form onSubmit={analyzeRetail} className="space-y-4">
          <div><label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">FICO Score</label>
            <input type="number" name="fico_score" value={retailForm.fico_score} onChange={handleRetailChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" /></div>
          <div className="flex gap-4">
            <div className="flex-1"><label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">LTV (%)</label>
              <input type="number" name="ltv" value={retailForm.ltv} onChange={handleRetailChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" /></div>
            <div className="flex-1"><label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">DTI (%)</label>
              <input type="number" name="dti" value={retailForm.dti} onChange={handleRetailChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" /></div>
          </div>
          <div><label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">Loan Amount ($)</label>
            <input type="number" name="loan_amount" value={retailForm.loan_amount} onChange={handleRetailChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" /></div>
          <div className="flex gap-4">
            <div className="flex-1"><label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">Rate (Dec)</label>
              <input type="number" step="0.001" name="interest_rate" value={retailForm.interest_rate} onChange={handleRetailChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" /></div>
            <div className="flex-1"><label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">Term (Mo)</label>
              <input type="number" name="term_months" value={retailForm.term_months} onChange={handleRetailChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" /></div>
          </div>
          <button type="submit" disabled={retailLoading} id="retail-btn" className="w-full bg-gold text-onyx-950 font-bold uppercase tracking-widest py-4 hover:bg-white transition-colors disabled:opacity-50 mt-4">
            {retailLoading ? "Training ML / Analyzing..." : "Run Credit Check"}</button>
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
    </>
  );

  // === RENDER: STRESS TESTING ===
  const SCENARIO_COLORS = { ccar_baseline: '#10b981', ccar_adverse: '#f59e0b', ccar_severely_adverse: '#ef4444', eba_adverse: '#f97316', pandemic: '#8b5cf6', rate_hike: '#3b82f6' };
  const renderStressTesting = () => (
    <>
      <div className="mb-12">
        <h1 className="text-5xl font-serif mb-4">CCAR / EBA Stress Testing</h1>
        <p className="text-ivory/50">Run a ticker through 6 macro-stress scenarios including CCAR Severely Adverse, Pandemic, and Rate Hike shocks.</p>
      </div>
      <form onSubmit={analyzeStress} className="relative max-w-xl mb-12">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-ivory/30"><Zap size={20} /></div>
        <input type="text" list="asset-list" className="w-full bg-onyx-900 border border-white/10 rounded-none py-4 pl-12 pr-32 text-lg focus:outline-none focus:border-gold transition-colors text-ivory uppercase"
          placeholder="E.G. AAPL, TSLA, NVDA" value={stressTicker} onChange={(e) => setStressTicker(e.target.value)} />
        <button type="submit" disabled={stressLoading} className="absolute inset-y-0 right-0 px-6 bg-gold text-onyx-950 font-bold uppercase tracking-widest text-sm hover:bg-white transition-colors disabled:opacity-50">
          {stressLoading ? "..." : "Search"}</button>
      </form>
      {error && <div className="p-4 bg-red-900/20 border border-red-500/50 text-red-200 mb-8 max-w-xl">{error}</div>}
      {stressResult ? (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <MetricCard title="Base PD" value={`${(stressResult.base_case.PD_rn * 100).toFixed(2)}%`} icon={<Target />} color="text-emerald-400" />
            <MetricCard title="Base DD" value={stressResult.base_case.DD_rn.toFixed(2)} icon={<Activity />} color="text-emerald-400" />
            <MetricCard title="Worst Scenario" value={stressResult.worst_case?.replace(/_/g, ' ').toUpperCase() || "N/A"} icon={<AlertTriangle />} color="text-red-400" />
            <MetricCard title="Base Asset Vol" value={`${(stressResult.base_case.sigma_V * 100).toFixed(1)}%`} icon={<BarChart3 />} />
          </div>
          <div className="p-6 bg-onyx-900/50 border border-white/5">
            <h4 className="text-xs uppercase tracking-widest text-gold mb-6">Scenario PD Comparison</h4>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={Object.entries(stressResult.scenario_results).map(([name, sc]) => ({
                name: name.replace(/_/g, ' '), PD: sc.PD_rn * 100, fill: SCENARIO_COLORS[name] || '#d4af37'
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" tick={{ fill: '#f5f5f0', fontSize: 10 }} angle={-15} textAnchor="end" height={60} />
                <YAxis tick={{ fill: '#f5f5f0', fontSize: 11 }} label={{ value: 'PD (%)', angle: -90, position: 'insideLeft', fill: '#f5f5f0', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid rgba(255,255,255,0.1)', color: '#f5f5f0' }} />
                <Bar dataKey="PD" name="Prob. of Default (%)">
                  {Object.entries(stressResult.scenario_results).map(([name], i) => (
                    <Cell key={i} fill={SCENARIO_COLORS[name] || '#d4af37'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="p-6 bg-onyx-900/50 border border-white/5 overflow-x-auto">
            <h4 className="text-xs uppercase tracking-widest text-gold mb-4">Detailed Scenario Results</h4>
            <table className="w-full text-sm">
              <thead><tr className="border-b border-white/10 text-ivory/50 text-xs uppercase tracking-widest">
                <th className="text-left py-3 pr-4">Scenario</th><th className="text-right py-3 px-4">PD</th><th className="text-right py-3 px-4">DD</th>
                <th className="text-right py-3 px-4">σ_V</th><th className="text-right py-3 px-4">D (stressed)</th><th className="text-right py-3 pl-4">r (stressed)</th>
              </tr></thead>
              <tbody>
                {Object.entries(stressResult.scenario_results).map(([name, sc]) => (
                  <tr key={name} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="py-3 pr-4 font-mono text-ivory/80 capitalize">{name.replace(/_/g, ' ')}</td>
                    <td className={`py-3 px-4 text-right font-mono ${sc.PD_rn > 0.05 ? 'text-red-400' : sc.PD_rn > 0.01 ? 'text-amber-400' : 'text-emerald-400'}`}>{(sc.PD_rn * 100).toFixed(3)}%</td>
                    <td className="py-3 px-4 text-right font-mono text-ivory/70">{sc.DD_rn.toFixed(2)}</td>
                    <td className="py-3 px-4 text-right font-mono text-ivory/70">{(sc.sigma_V * 100).toFixed(1)}%</td>
                    <td className="py-3 px-4 text-right font-mono text-ivory/70">${(sc.D_stressed / 1e9).toFixed(2)}B</td>
                    <td className="py-3 pl-4 text-right font-mono text-ivory/70">{(sc.r_stressed * 100).toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      ) : (
        <div className="flex flex-col items-center justify-center text-ivory/30 pb-10">
          <Zap size={48} className="mb-4 opacity-50" />
          <p className="text-xl font-serif">Enter a ticker to run CCAR/EBA stress scenarios.</p>
          <p className="text-sm mt-2 text-ivory/20">Covers Baseline, Adverse, Severely Adverse, EBA, Pandemic, and Rate Hike shocks.</p>
        </div>
      )}
    </>
  );

  // === RENDER: PRIVATE EQUITY ===
  const renderPrivateEquity = () => (
    <>
      <form onSubmit={handlePeSearch} className="relative max-w-xl mb-12">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-ivory/30"><Search size={20} /></div>
        <input type="text" list="pe-list" className="w-full bg-onyx-900 border border-white/10 rounded-none py-4 pl-12 pr-32 text-lg focus:outline-none focus:border-gold transition-colors text-ivory uppercase"
          placeholder="SEARCH PRIVATE COMPANY OR LBO..." value={peSearch} onChange={(e) => setPeSearch(e.target.value)} />
        <datalist id="pe-list">{sortedPe.map(a => <option key={a.ticker} value={a.ticker}>{a.name} ({a.sector})</option>)}</datalist>
        <button type="submit" className="absolute inset-y-0 right-0 px-6 bg-gold text-onyx-950 font-bold uppercase tracking-widest text-sm hover:bg-white transition-colors">
          Search</button>
      </form>
    <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="flex flex-col md:flex-row gap-12">
      <div className="w-full md:w-1/3">
        <h2 className="font-serif text-2xl mb-6 text-gold">Portfolio Company</h2>
        <form onSubmit={analyzePE} className="space-y-4">
          <div><label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">Company Name</label>
            <input type="text" name="name" value={peForm.name} onChange={handlePeChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" /></div>
          <div className="flex gap-4">
            <div className="flex-1"><label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">Sector</label>
              <select name="sector" value={peForm.sector} onChange={handlePeChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none">
                <option>Tech</option><option>Healthcare</option><option>Industrials</option><option>Consumer</option><option>Energy</option><option>Financials</option>
              </select></div>
            <div className="flex-1"><label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">Geography</label>
              <select name="geography" value={peForm.geography} onChange={handlePeChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none">
                <option>US</option><option>EU</option><option>Asia</option>
              </select></div>
          </div>
          <div className="flex gap-4">
            <div className="flex-1"><label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">EBITDA ($M)</label>
              <input type="number" name="ebitda" value={peForm.ebitda} onChange={handlePeChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" /></div>
            <div className="flex-1"><label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">Total Debt ($M)</label>
              <input type="number" name="total_debt" value={peForm.total_debt} onChange={handlePeChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" /></div>
          </div>
          <div className="flex gap-4">
            <div className="flex-1"><label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">Equity BV ($M)</label>
              <input type="number" name="equity_book_value" value={peForm.equity_book_value} onChange={handlePeChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" /></div>
            <div className="flex-1"><label className="block text-xs uppercase tracking-widest text-ivory/50 mb-1">Revenue ($M)</label>
              <input type="number" name="revenue" value={peForm.revenue} onChange={handlePeChange} className="w-full bg-onyx-900 border border-white/10 p-3 text-ivory focus:border-gold outline-none" /></div>
          </div>
          <button type="submit" disabled={peLoading} id="pe-btn" className="w-full bg-gold text-onyx-950 font-bold uppercase tracking-widest py-4 hover:bg-white transition-colors disabled:opacity-50 mt-4">
            {peLoading ? "Running Moody's Model..." : "Analyze Company"}</button>
          <button type="button" onClick={loadSampleLBO} className="w-full border border-gold/30 text-gold font-bold uppercase tracking-widest py-3 hover:bg-gold/10 transition-colors text-sm">
            Load Sample LBO Deal</button>
        </form>
      </div>
      <div className="w-full md:w-2/3">
        {peResult ? (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <h2 className="font-serif text-2xl text-ivory/90 mb-2">{peResult.name}</h2>
            <p className="text-xs text-ivory/40 uppercase tracking-widest mb-6">{peResult.methodology}</p>
            <div className="grid grid-cols-2 gap-6">
              <MetricCard title="Distance to Default" value={peResult.DD?.toFixed(2) || "N/A"} icon={<Target />} color={peResult.DD < 2 ? "text-red-400" : "text-emerald-400"} />
              <MetricCard title="Prob. of Default (1Y)" value={peResult.PD != null ? `${(peResult.PD * 100).toFixed(3)}%` : "N/A"} icon={<AlertTriangle />} color="text-red-400" />
              <MetricCard title="Enterprise Value (Proxy)" value={`$${peResult.V_proxy?.toFixed(0) || 0}M`} icon={<Building2 />} color="text-gold" />
              <MetricCard title="Asset Volatility" value={`${((peResult.sigma_V || 0) * 100).toFixed(1)}%`} icon={<Activity />} />
            </div>
            {peResult.peer_multiples && Object.keys(peResult.peer_multiples).length > 0 && (
              <div className="p-6 bg-onyx-900/50 border border-white/5">
                <h4 className="text-xs uppercase tracking-widest text-gold mb-4">Peer Comparable Multiples</h4>
                <div className="grid grid-cols-3 gap-4">
                  {Object.entries(peResult.peer_multiples).map(([k, v]) => (
                    <div key={k} className="text-center">
                      <div className="text-xs text-ivory/50 mb-1">{k.replace(/_/g, ' ')}</div>
                      <div className="text-xl font-serif text-ivory">{typeof v === 'number' ? v.toFixed(2) : v}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {peResult.pd_term_structure && Object.keys(peResult.pd_term_structure).length > 0 && (
              <div className="p-6 bg-onyx-900/50 border border-white/5">
                <h4 className="text-xs uppercase tracking-widest text-gold mb-4">PD Term Structure</h4>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={Object.entries(peResult.pd_term_structure).sort((a,b) => a[0]-b[0]).map(([h, pd]) => ({ horizon: `${h}Y`, pd: pd * 100 }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="horizon" tick={{ fill: '#f5f5f0', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#f5f5f0', fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid rgba(255,255,255,0.1)', color: '#f5f5f0' }} />
                    <Area type="monotone" dataKey="pd" stroke="#d4af37" fill="rgba(212,175,55,0.15)" name="PD (%)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
            <div className="p-6 bg-onyx-900/50 border border-white/5 text-sm text-ivory/70 leading-relaxed">
              <strong>Methodology:</strong> The Moody's Private Firm Model proxies enterprise value (V) via EBITDA × peer EV/EBITDA multiple, and asset volatility (σ_V) by Hamada-unlevering the median peer equity volatility. Distance to Default is computed using the structural Merton framework without requiring traded equity.
            </div>
          </motion.div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-ivory/30 border border-white/5 bg-onyx-900/20 p-12">
            <Briefcase size={48} className="mb-4 opacity-50" />
            <p className="text-xl font-serif text-center">Private Equity Risk Module</p>
            <p className="text-sm mt-2 text-center max-w-md">Input portfolio company financials to estimate DD and PD using the Moody's Private Firm Model with GICS-matched peer comps.</p>
          </div>
        )}
        {lboResult && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mt-8 space-y-6">
            <h3 className="text-sm font-bold uppercase tracking-widest text-gold border-b border-white/5 pb-4">LBO Debt Amortization — {lboResult.company_name}</h3>
            <div className="p-6 bg-onyx-900/50 border border-white/5">
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={lboResult.schedule.map((s, i) => ({ quarter: `Q${i+1}`, debt: s.total_debt }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="quarter" tick={{ fill: '#f5f5f0', fontSize: 10 }} />
                  <YAxis tick={{ fill: '#f5f5f0', fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid rgba(255,255,255,0.1)', color: '#f5f5f0' }} />
                  <Area type="monotone" dataKey="debt" stroke="#ef4444" fill="rgba(239,68,68,0.15)" name="Total Debt ($M)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            {lboResult.maturity_wall && (
              <div className="grid grid-cols-3 gap-6">
                <MetricCard title="Nearest Maturity" value={`${lboResult.maturity_wall.nearest_maturity_years} yrs`} icon={<AlertTriangle />} color="text-amber-400" />
                <MetricCard title="Refinancing Risk" value={lboResult.maturity_wall.refinancing_risk} icon={<Shield />} color={lboResult.maturity_wall.refinancing_risk === 'HIGH' ? 'text-red-400' : 'text-emerald-400'} />
                <MetricCard title="Maturity Profile" value={Object.entries(lboResult.maturity_wall.maturity_profile).map(([yr, amt]) => `Y${yr}: $${amt}M`).join(' | ')} icon={<BarChart3 />} />
              </div>
            )}
          </motion.div>
        )}
      </div>
    </motion.div>
    </>
  );

  const TABS = [
    { key: 'multi-asset', label: 'Multi-Asset & NLP' },
    { key: 'corporate', label: 'Corporate EWS' },
    { key: 'stress-testing', label: 'Stress Testing' },
    { key: 'retail', label: 'Retail Credit' },
    { key: 'private-equity', label: 'Private Equity' }
  ];

  return (
    <div className="min-h-screen bg-onyx-950 text-ivory font-sans selection:bg-gold selection:text-onyx-950 flex flex-col">
      <nav className="border-b border-white/5 bg-onyx-950/80 backdrop-blur-md sticky top-0 z-50 p-6 flex justify-between items-center">
        <Link to="/" className="flex items-center gap-2 hover:text-gold transition-colors">
          <ChevronLeft size={20} />
          <span className="text-sm tracking-[0.2em] uppercase">Back to Hub</span>
        </Link>
        <div className="text-sm font-serif tracking-widest text-gold uppercase flex items-center gap-4 flex-wrap">
          {TABS.map((tab, i) => (
            <React.Fragment key={tab.key}>
              {i > 0 && <span className="text-ivory/10">|</span>}
              <button onClick={() => { setActiveTab(tab.key); setError(null); }} className={`transition-colors ${activeTab === tab.key ? 'text-gold' : 'text-ivory/30 hover:text-ivory/60'}`}>{tab.label}</button>
            </React.Fragment>
          ))}
        </div>
      </nav>

      <main className="flex-1 max-w-7xl w-full mx-auto p-8 flex flex-col">
        <AnimatePresence mode="wait">
          <motion.div key={activeTab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
            {activeTab === 'multi-asset' && (<>
              <div className="mb-12"><h1 className="text-5xl font-serif mb-4">Quantitative Risk Engine</h1><p className="text-ivory/50">Real-time asset modeling using Merton/KMV and FinBERT SEC Sentiment.</p></div>
              <form onSubmit={analyzeTicker} className="relative max-w-xl mb-12">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-ivory/30"><Search size={20} /></div>
                <input type="text" list="asset-list" className="w-full bg-onyx-900 border border-white/10 rounded-none py-4 pl-12 pr-32 text-lg focus:outline-none focus:border-gold transition-colors text-ivory uppercase"
                  placeholder="E.G. AAPL, ^TNX, VOO" value={ticker} onChange={(e) => setTicker(e.target.value)} />
                <datalist id="asset-list">{sortedAssets.map(a => <option key={a.ticker} value={a.ticker}>{a.name}</option>)}</datalist>
                <button id="analyze-btn" type="submit" disabled={loading} className="absolute inset-y-0 right-0 px-6 bg-gold text-onyx-950 font-bold uppercase tracking-widest text-sm hover:bg-white transition-colors disabled:opacity-50">
                  {loading ? "..." : "Search"}</button>
              </form>
              {error && <div className="p-4 bg-red-900/20 border border-red-500/50 text-red-200 mb-8 max-w-xl">{error}</div>}
              <div className="flex-1">{renderMultiAsset()}</div>
            </>)}
            {activeTab === 'corporate' && (<>
              <div className="mb-12"><h1 className="text-5xl font-serif mb-4">Corporate EWS</h1><p className="text-ivory/50">Early Warning System using Ensemble (Merton + Altman Z-Score) with Basel IRB, TTC/PIT, and CECL overlays.</p></div>
              <form onSubmit={analyzeCorporate} className="relative max-w-xl mb-12">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-ivory/30"><Search size={20} /></div>
                <input type="text" list="asset-list" className="w-full bg-onyx-900 border border-white/10 rounded-none py-4 pl-12 pr-32 text-lg focus:outline-none focus:border-gold transition-colors text-ivory uppercase"
                  placeholder="E.G. TSLA, NVDA" value={corporateTicker} onChange={(e) => setCorporateTicker(e.target.value)} />
                <button id="corp-analyze-btn" type="submit" disabled={corporateLoading} className="absolute inset-y-0 right-0 px-6 bg-gold text-onyx-950 font-bold uppercase tracking-widest text-sm hover:bg-white transition-colors disabled:opacity-50">
                  {corporateLoading ? "..." : "Search"}</button>
              </form>
              {error && <div className="p-4 bg-red-900/20 border border-red-500/50 text-red-200 mb-8 max-w-xl">{error}</div>}
              <div className="flex-1">{renderCorporate()}</div>
            </>)}
            {activeTab === 'stress-testing' && renderStressTesting()}
            {activeTab === 'retail' && (<>
              <div className="mb-12"><h1 className="text-5xl font-serif mb-4">Retail Credit Check</h1><p className="text-ivory/50">Mortgage risk analysis using Expected Loss (EL) models.</p></div>
              {error && <div className="p-4 bg-red-900/20 border border-red-500/50 text-red-200 mb-8 max-w-xl">{error}</div>}
              {renderRetail()}
            </>)}
            {activeTab === 'private-equity' && (<>
              <div className="mb-12"><h1 className="text-5xl font-serif mb-4">Private Equity Risk</h1><p className="text-ivory/50">Moody's Private Firm Model with GICS-matched peer comps, Hamada-unlevered vol, and LBO debt schedule analysis.</p></div>
              {error && <div className="p-4 bg-red-900/20 border border-red-500/50 text-red-200 mb-8 max-w-xl">{error}</div>}
              {renderPrivateEquity()}
            </>)}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

function MetricCard({ title, value, icon, color = "text-gold" }) {
  return (
    <div className="bg-onyx-900/50 border border-white/5 p-6 relative overflow-hidden group hover:border-gold/30 transition-colors">
      <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity ${color}`}>{icon}</div>
      <div className="text-xs uppercase tracking-[0.2em] text-ivory/50 mb-4">{title}</div>
      <div className={`text-4xl font-light font-serif ${color}`}>{value || "—"}</div>
    </div>
  );
}
