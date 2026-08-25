import re

with open('frontend/src/Dashboard.jsx', 'r') as f:
    content = f.read()

# 1. Imports: Add new icons
old_imports = """from lucide-react";"""
new_imports = """, Home, DollarSign, Calculator, Layers } from "lucide-react";"""
content = content.replace(old_imports, new_imports)

# 2. Add State for Tabs and Retail Form
state_block = """  const [loading, setLoading] = useState(false);"""
new_state = """  const [activeTab, setActiveTab] = useState("multi-asset");
  
  // Retail Form State
  const [retailForm, setRetailForm] = useState({
    fico_score: 720, ltv: 80, dti: 35, loan_amount: 350000, interest_rate: 0.055, term_months: 360, months_seasoned: 12
  });
  const [retailResult, setRetailResult] = useState(null);
  const [retailLoading, setRetailLoading] = useState(false);

  const [loading, setLoading] = useState(false);"""
content = content.replace(state_block, new_state)

# 3. Add Retail Analyze Function
analyze_block = """  const analyzeTicker = async (e) => {"""
retail_analyze = """  const analyzeRetail = async (e) => {
    e.preventDefault();
    setRetailLoading(true);
    setError(null);
    setRetailResult(null);
    try {
      const payload = {
        loans: [{ loan_id: "LOAN-1", ...retailForm }]
      };
      const res = await axios.post(`http://127.0.0.1:8000/api/v1/risk/retail/portfolio`, payload);
      setRetailResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to analyze retail loan.");
    } finally {
      setRetailLoading(false);
    }
  };

  const analyzeTicker = async (e) => {"""
content = content.replace(analyze_block, retail_analyze)

# 4. Modify the renderContent function to add Retail UI. Actually, it's easier to rewrite the `main` section.
# Instead of Regex replacement which is brittle, I'll rewrite the entire file since it's short.
