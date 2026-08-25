import re

with open('frontend/src/Dashboard.jsx', 'r') as f:
    content = f.read()

old_metrics = """            <MetricCard title="Market Cap" value={`$${(metrics.V_current / 1e9).toFixed(1)}B`} icon={<BarChart3 />} />"""

new_metrics = """            <MetricCard title="Market Cap" value={`$${(metrics.V_current / 1e9).toFixed(1)}B`} icon={<BarChart3 />} />
            <MetricCard title="FinBERT Sentiment" value={metrics.sentiment_score !== undefined ? metrics.sentiment_score.toFixed(2) : "N/A"} icon={<Activity />} color={metrics.sentiment_score < 0 ? "text-red-400" : "text-emerald-400"} />"""

content = content.replace(old_metrics, new_metrics)

with open('frontend/src/Dashboard.jsx', 'w') as f:
    f.write(content)
