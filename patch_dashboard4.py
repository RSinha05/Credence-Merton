import re

with open('frontend/src/Dashboard.jsx', 'r') as f:
    content = f.read()

state_inject = """  const [corporateTicker, setCorporateTicker] = useState("");
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
"""

content = content.replace("  const analyzeTicker = async (e) => {", state_inject + "\n  const analyzeTicker = async (e) => {")

with open('frontend/src/Dashboard.jsx', 'w') as f:
    f.write(content)
