import React, { useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, Search, Activity, BarChart3, Target, Shield, AlertTriangle } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function Dashboard() {
  const [ticker, setTicker] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

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

  const renderContent = () => {
    if (!result) return (
      <div className="flex flex-col items-center justify-center h-full text-ivory/30 pt-20">
        <Activity size={48} className="mb-4 opacity-50" />
        <p className="text-xl font-serif">Enter a ticker to begin quantitative analysis.</p>
        <p className="text-sm mt-2">Supports Global Equities, Sovereign Bonds, and ETFs.</p>
      </div>
    );

    const { asset_type, metrics, risk_tier, ticker: t } = result;

    if (asset_type === "EQUITY") {
      return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <MetricCard title="Distance to Default (DD)" value={metrics.DD_rn?.toFixed(2)} icon={<Target />} color="text-emerald-400" />
            <MetricCard title="Prob. of Default (1Y)" value={`${(metrics.PD_rn * 100).toFixed(2)}%`} icon={<AlertTriangle />} color="text-red-400" />
            <MetricCard title="Asset Volatility" value={`${(metrics.sigma_V * 100).toFixed(2)}%`} icon={<Activity />} />
            <MetricCard title="Market Cap" value={`$${(metrics.V_current / 1e9).toFixed(1)}B`} icon={<BarChart3 />} />
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

  return (
    <div className="min-h-screen bg-onyx-950 text-ivory font-sans selection:bg-gold selection:text-onyx-950 flex flex-col">
      <nav className="border-b border-white/5 bg-onyx-950/80 backdrop-blur-md sticky top-0 z-50 p-6 flex justify-between items-center">
        <Link to="/" className="flex items-center gap-2 hover:text-gold transition-colors">
          <ChevronLeft size={20} />
          <span className="text-sm tracking-[0.2em] uppercase">Back to Hub</span>
        </Link>
        <div className="text-xl font-serif tracking-widest text-gold uppercase">Blackswan Nova</div>
      </nav>

      <main className="flex-1 max-w-7xl w-full mx-auto p-8 flex flex-col">
        <div className="mb-12">
          <h1 className="text-5xl font-serif mb-4">Quantitative Risk Engine</h1>
          <p className="text-ivory/50">Real-time asset modeling using Merton/KMV and historical VaR simulations.</p>
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
            type="submit"
            disabled={loading}
            className="absolute inset-y-0 right-0 px-6 bg-gold text-onyx-950 font-bold uppercase tracking-widest text-sm hover:bg-white transition-colors disabled:opacity-50"
          >
            {loading ? "..." : "Analyze"}
          </button>
        </form>

        <AnimatePresence>
          {error && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="p-4 bg-red-900/20 border border-red-500/50 text-red-200 mb-8 max-w-xl">
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex-1">
          {renderContent()}
        </div>
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
