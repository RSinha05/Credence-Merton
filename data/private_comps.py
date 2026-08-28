import logging
from dataclasses import dataclass
from typing import List, Dict, Any
import numpy as np

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class PrivateCompany:
    """
    Represents a private portfolio company.
    """
    name: str
    sector: str  # GICS sector
    geography: str  # e.g., 'US', 'EU'
    ebitda: float  # in millions
    total_debt: float
    equity_book_value: float
    revenue: float

@dataclass
class PublicComp:
    """
    Represents a public comparable company.
    """
    ticker: str
    name: str
    sector: str
    geography: str
    market_cap: float
    ev_ebitda_multiple: float
    equity_vol: float  # annualized
    leverage_ratio: float  # D/E
    ebitda: float

# Universe of public comparable companies spanning multiple sectors
COMP_UNIVERSE: List[PublicComp] = [
    PublicComp("TWTR", "Twitter (LBO)", "Tech", "US", 44000.0, 45.0, 0.45, 2.5, 977.8),
    PublicComp("VMW", "VMware (Acq)", "Tech", "US", 61000.0, 22.0, 0.3, 1.2, 2772.7),
    PublicComp("CTXS", "Citrix (LBO)", "Tech", "US", 16500.0, 18.5, 0.35, 3.5, 891.9),
    PublicComp("SPLK", "Splunk (Acq)", "Tech", "US", 28000.0, 25.0, 0.4, 1.0, 1120.0),
    PublicComp("WORK", "Slack (Acq)", "Tech", "US", 27700.0, 35.0, 0.45, 0.5, 791.4),
    PublicComp("DATA", "Tableau (Acq)", "Tech", "US", 15700.0, 30.0, 0.38, 0.8, 523.3),
    PublicComp("RHT", "Red Hat (Acq)", "Tech", "US", 34000.0, 28.0, 0.32, 0.9, 1214.3),
    PublicComp("HEXA.NS", "Hexaware (LBO)", "Tech", "IND", 2500.0, 15.0, 0.3, 2.0, 166.7),
    PublicComp("MPHASIS.NS", "Mphasis (LBO)", "Tech", "IND", 4000.0, 16.5, 0.28, 1.5, 242.4),
    PublicComp("MINDTREE.NS", "Mindtree (Acq)", "Tech", "IND", 3500.0, 18.0, 0.25, 0.5, 194.4),
    PublicComp("MCAF", "McAfee (LBO)", "Tech", "US", 14000.0, 12.0, 0.28, 4.0, 1166.7),
    PublicComp("SYMC", "Symantec (Acq)", "Tech", "US", 10700.0, 14.0, 0.3, 2.2, 764.3),
    PublicComp("FLPK.NS", "Flipkart (Acq)", "Consumer", "IND", 16000.0, 40.0, 0.5, 1.0, 400.0),
    PublicComp("XM", "Qualtrics (LBO)", "Tech", "US", 12500.0, 20.0, 0.38, 2.5, 625.0),
    PublicComp("MORN", "Morningstar (Acq)", "Equity Services", "US", 12000.0, 22.0, 0.25, 1.0, 545.5),
    PublicComp("INFO.NS", "Info Edge (Acq)", "Equity Services", "IND", 8000.0, 25.0, 0.3, 0.5, 320.0),
    PublicComp("FDS", "FactSet (Acq)", "Equity Services", "US", 16000.0, 24.0, 0.22, 1.2, 666.7),
    PublicComp("MSCI", "MSCI Inc", "Equity Services", "US", 40000.0, 30.0, 0.24, 2.0, 1333.3),
    PublicComp("SPGI", "S&P Global", "Equity Services", "US", 120000.0, 25.0, 0.2, 1.5, 4800.0),
    PublicComp("MCO", "Moody's Corp", "Equity Services", "US", 65000.0, 26.0, 0.22, 1.8, 2500.0),
    PublicComp("CRISIL.NS", "CRISIL", "Equity Services", "IND", 3500.0, 28.0, 0.2, 0.2, 125.0),
    PublicComp("CARE.NS", "CARE Ratings", "Equity Services", "IND", 500.0, 15.0, 0.25, 0.1, 33.3),
    PublicComp("ICRA.NS", "ICRA Ltd", "Equity Services", "IND", 600.0, 20.0, 0.24, 0.1, 30.0),
    PublicComp("ARM", "Arm (LBO)", "Tech", "US", 65000.0, 35.0, 0.4, 0.5, 1857.1),
    PublicComp("TDC", "Teradata (Acq Target)", "Tech", "US", 4000.0, 12.0, 0.3, 1.5, 333.3),
    PublicComp("NICE", "NICE Systems", "Tech", "US", 15000.0, 20.0, 0.25, 1.0, 750.0),
    PublicComp("ZBRA", "Zebra Technologies", "Tech", "US", 13000.0, 18.0, 0.35, 1.2, 722.2),
    PublicComp("AAPL", "Apple Inc.", "Tech", "US", 1309290.1, 16.9, 0.24, 0.6, 77472.8),
    PublicComp("MSFT", "Microsoft", "Tech", "US", 909487.0, 17.4, 0.32, 1.2, 52269.4),
    PublicComp("AMZN", "Amazon", "Consumer", "US", 1327386.5, 10.8, 0.22, 1.6, 122906.2),
    PublicComp("NVDA", "NVIDIA", "Tech", "US", 712855.1, 12.9, 0.41, 1.9, 55260.1),
    PublicComp("META", "Meta", "Tech", "US", 933318.7, 26.0, 0.33, 2.1, 35896.9),
    PublicComp("GOOGL", "Alphabet", "Tech", "US", 197916.6, 23.3, 0.4, 0.5, 8494.3),
    PublicComp("TSLA", "Tesla", "Consumer", "US", 1646893.9, 17.9, 0.29, 1.9, 92005.2),
    PublicComp("AVGO", "Broadcom", "Tech", "US", 1197593.4, 27.2, 0.32, 1.9, 44029.2),
    PublicComp("PEP", "PepsiCo", "Consumer", "US", 1899104.8, 14.3, 0.25, 0.1, 132804.5),
    PublicComp("COST", "Costco", "Consumer", "US", 705664.2, 21.5, 0.43, 1.5, 32821.6),
    PublicComp("CSCO", "Cisco", "Tech", "US", 471794.9, 23.7, 0.37, 1.1, 19907.0),
    PublicComp("TMUS", "T-Mobile", "Tech", "US", 1569794.8, 12.0, 0.24, 0.9, 130816.2),
    PublicComp("ADBE", "Adobe", "Tech", "US", 995137.6, 21.6, 0.44, 0.8, 46071.2),
    PublicComp("TXN", "Texas Instruments", "Tech", "US", 928075.0, 21.2, 0.16, 1.2, 43777.1),
    PublicComp("CMCSA", "Comcast", "Consumer", "US", 154634.0, 29.0, 0.39, 0.2, 5332.2),
    PublicComp("AMGN", "Amgen", "Healthcare", "US", 1429616.1, 28.0, 0.4, 0.6, 51057.7),
    PublicComp("INTU", "Intuit", "Tech", "US", 21796.9, 19.9, 0.29, 2.3, 1095.3),
    PublicComp("INTC", "Intel", "Tech", "US", 55636.5, 25.7, 0.23, 0.8, 2164.8),
    PublicComp("QCOM", "Qualcomm", "Tech", "US", 1117401.6, 19.5, 0.24, 1.2, 57302.6),
    PublicComp("HON", "Honeywell", "Industrials", "US", 1406782.8, 18.8, 0.36, 1.9, 74828.9),
    PublicComp("SBUX", "Starbucks", "Consumer", "US", 496337.6, 19.4, 0.37, 1.9, 25584.4),
    PublicComp("GILD", "Gilead Sciences", "Healthcare", "US", 353823.5, 14.8, 0.24, 0.9, 23907.0),
    PublicComp("MDLZ", "Mondelez", "Consumer", "US", 1065990.9, 13.0, 0.34, 1.1, 81999.3),
    PublicComp("NFLX", "Netflix", "Tech", "US", 164436.4, 10.9, 0.39, 0.8, 15085.9),
    PublicComp("AMAT", "Applied Materials", "Tech", "US", 1778359.0, 23.5, 0.41, 1.3, 75674.9),
    PublicComp("ISRG", "Intuitive Surgical", "Healthcare", "US", 986974.2, 21.9, 0.26, 2.4, 45067.3),
    PublicComp("ADP", "ADP", "Tech", "US", 1658950.2, 13.2, 0.18, 0.8, 125678.0),
    PublicComp("VRTX", "Vertex Pharma", "Healthcare", "US", 612923.0, 20.3, 0.3, 1.2, 30193.3),
    PublicComp("REGN", "Regeneron", "Healthcare", "US", 412847.7, 22.9, 0.28, 0.7, 18028.3),
    PublicComp("ADI", "Analog Devices", "Tech", "US", 1142953.0, 18.2, 0.4, 0.2, 62799.6),
    PublicComp("RELIANCE.NS", "Reliance Ind", "Energy", "IND", 167124.4, 21.3, 0.48, 1.1, 7846.2),
    PublicComp("TCS.NS", "TCS", "Tech", "IND", 26588.3, 12.2, 0.21, 0.7, 2179.4),
    PublicComp("HDFCBANK.NS", "HDFC Bank", "Financials", "IND", 76018.5, 22.2, 0.27, 2.4, 3424.3),
    PublicComp("ICICIBANK.NS", "ICICI Bank", "Financials", "IND", 182945.6, 13.0, 0.27, 2.6, 14072.7),
    PublicComp("INFY.NS", "Infosys", "Tech", "IND", 108456.7, 24.3, 0.4, 0.8, 4463.2),
    PublicComp("ITC.NS", "ITC", "Consumer", "IND", 40577.5, 21.1, 0.47, 2.5, 1923.1),
    PublicComp("SBIN.NS", "State Bank of India", "Financials", "IND", 196630.4, 14.4, 0.34, 0.6, 13654.9),
    PublicComp("BHARTIARTL.NS", "Bharti Airtel", "Tech", "IND", 194446.8, 12.9, 0.24, 0.7, 15073.4),
    PublicComp("KOTAKBANK.NS", "Kotak Mahindra", "Financials", "IND", 51986.3, 13.1, 0.23, 0.5, 3968.4),
    PublicComp("LT.NS", "Larsen & Toubro", "Industrials", "IND", 158045.0, 23.7, 0.3, 2.3, 6668.6),
    PublicComp("AXISBANK.NS", "Axis Bank", "Financials", "IND", 82786.3, 17.7, 0.31, 1.4, 4677.2),
    PublicComp("HINDUNILVR.NS", "HUL", "Consumer", "IND", 178052.8, 23.3, 0.49, 2.6, 7641.8),
    PublicComp("BAJFINANCE.NS", "Bajaj Finance", "Financials", "IND", 136195.8, 19.3, 0.27, 1.1, 7056.8),
    PublicComp("MARUTI.NS", "Maruti Suzuki", "Consumer", "IND", 106602.4, 16.1, 0.32, 0.9, 6621.3),
    PublicComp("SUNPHARMA.NS", "Sun Pharma", "Healthcare", "IND", 126722.1, 9.0, 0.42, 0.5, 14080.2),
    PublicComp("TITAN.NS", "Titan", "Consumer", "IND", 103902.2, 13.7, 0.41, 1.4, 7584.1),
    PublicComp("ASIANPAINT.NS", "Asian Paints", "Consumer", "IND", 44162.3, 15.2, 0.22, 0.5, 2905.4),
    PublicComp("WIPRO.NS", "Wipro", "Tech", "IND", 40433.9, 17.5, 0.24, 2.4, 2310.5),
    PublicComp("HCLTECH.NS", "HCL Tech", "Tech", "IND", 48626.1, 24.6, 0.24, 0.2, 1976.7),
    PublicComp("BAJAJFINSV.NS", "Bajaj Finserv", "Financials", "IND", 88960.6, 19.1, 0.22, 2.4, 4657.6),
    PublicComp("NESTLEIND.NS", "Nestle India", "Consumer", "IND", 57042.1, 13.6, 0.18, 2.3, 4194.3),
    PublicComp("JSWL41.NS", "JSW Lifestyle India", "Consumer", "IND", 6808.0, 23.8, 0.26, 4.1, 286.1),
    PublicComp("QDC71", "Quantum Diagnostics Corp", "Healthcare", "US", 2435.2, 17.6, 0.38, 2.1, 138.4),
    PublicComp("BTLL27", "Blackstone Trust LLC", "Financials", "US", 8509.8, 23.6, 0.42, 5.0, 360.6),
    PublicComp("TVSE16.NS", "TVS Exchange Ltd", "Equity Services", "IND", 28296.7, 8.4, 0.47, 4.8, 3368.7),
    PublicComp("GMRA44.NS", "GMR Asset Industries", "Financials", "IND", 24498.9, 7.7, 0.3, 2.6, 3181.7),
    PublicComp("LTBI30.NS", "L&T Bank India", "Energy", "IND", 34154.8, 23.1, 0.38, 4.1, 1478.6),
    PublicComp("PAG60", "Pinnacle Asset Group", "Financials", "US", 44877.3, 17.8, 0.51, 3.6, 2521.2),
    PublicComp("KKRA87", "KKR Apparel Corp", "Consumer", "US", 27800.6, 18.2, 0.28, 1.4, 1527.5),
    PublicComp("CNC85", "Crest Networks Corp", "Tech", "US", 10494.0, 21.5, 0.43, 1.6, 488.1),
    PublicComp("GLI69.NS", "Godrej Lifestyle India", "Consumer", "IND", 16491.3, 22.4, 0.48, 2.4, 736.2),
    PublicComp("ALL56.NS", "Adani Lifestyle Ltd", "Consumer", "IND", 9253.6, 13.7, 0.2, 3.1, 675.4),
    PublicComp("BDL57.NS", "Birla Digital Ltd", "Tech", "IND", 1601.2, 20.1, 0.26, 3.9, 79.7),
    PublicComp("RAE83.NS", "Reliance Analytics Enterprises", "Equity Services", "IND", 5994.9, 15.2, 0.38, 4.3, 394.4),
    PublicComp("BAL40.NS", "Bajaj Analytics Ltd", "Equity Services", "IND", 5380.7, 8.3, 0.2, 5.1, 648.3),
    PublicComp("VPG54", "Vertex Partners Group", "Energy", "US", 44656.1, 10.2, 0.37, 3.3, 4378.0),
    PublicComp("JSWC39.NS", "JSW Capital Ltd", "Financials", "IND", 23805.5, 16.5, 0.38, 3.8, 1442.8),
    PublicComp("ADG38", "Apollo Digital Group", "Tech", "US", 17201.3, 22.8, 0.53, 3.3, 754.4),
    PublicComp("JSWC34.NS", "JSW Cloud Enterprises", "Tech", "IND", 6628.6, 13.5, 0.43, 4.0, 491.0),
    PublicComp("BTL13.NS", "Bajaj Trust Ltd", "Financials", "IND", 48462.1, 14.4, 0.57, 1.9, 3365.4),
    PublicComp("ACI35.NS", "Adani Corp Industries", "Industrials", "IND", 10251.5, 7.1, 0.25, 2.7, 1443.9),
    PublicComp("ABI66.NS", "Adani Bio India", "Healthcare", "IND", 16533.0, 21.4, 0.52, 1.4, 772.6),
    PublicComp("JSWH39.NS", "JSW Health Enterprises", "Healthcare", "IND", 38391.2, 8.4, 0.29, 3.8, 4570.4),
    PublicComp("NCG27", "Nova Credit Group", "Financials", "US", 31498.7, 12.9, 0.38, 5.7, 2441.8),
    PublicComp("BBL91.NS", "Bajaj Brokers Ltd", "Equity Services", "IND", 32646.5, 8.8, 0.4, 4.4, 3709.8),
    PublicComp("CEG13", "Carlyle Exchange Group", "Equity Services", "US", 13828.2, 14.2, 0.59, 5.8, 973.8),
    PublicComp("BMI23.NS", "Bajaj Mfg Industries", "Industrials", "IND", 9971.3, 23.0, 0.52, 4.7, 433.5),
    PublicComp("TVSH73.NS", "TVS Heavy Industries", "Industrials", "IND", 46855.2, 15.3, 0.25, 3.7, 3062.4),
    PublicComp("NSC37", "Nova Sys Corp", "Tech", "US", 27901.9, 19.6, 0.58, 4.0, 1423.6),
    PublicComp("TEI59.NS", "Tata Equities Industries", "Financials", "IND", 39624.7, 19.3, 0.54, 3.0, 2053.1),
    PublicComp("TCI14.NS", "Tata Cloud Industries", "Tech", "IND", 10952.3, 14.8, 0.42, 3.1, 740.0),
    PublicComp("STLL48", "Stellar Trust LLC", "Financials", "US", 4251.2, 15.8, 0.34, 3.1, 269.1),
    PublicComp("CAIH21", "Carlyle AI Holdings", "Tech", "US", 38100.9, 22.4, 0.35, 2.7, 1700.9),
    PublicComp("AGC64", "Acme Goods Corp", "Consumer", "US", 14785.7, 20.6, 0.42, 3.5, 717.8),
    PublicComp("VCH59", "Vertex Credit Holdings", "Energy", "US", 20007.7, 20.6, 0.52, 2.2, 971.2),
    PublicComp("CTI53", "Carlyle Trust Inc", "Energy", "US", 5646.1, 19.5, 0.21, 4.4, 289.5),
    PublicComp("RPL97.NS", "Reliance Pharma Ltd", "Healthcare", "IND", 16789.7, 23.2, 0.25, 2.1, 723.7),
    PublicComp("LTAI72.NS", "L&T Aero India", "Industrials", "IND", 47295.1, 24.7, 0.46, 3.8, 1914.8),
    PublicComp("CGH56", "Crest Global Holdings", "Equity Services", "US", 8082.2, 21.3, 0.27, 5.7, 379.4),
    PublicComp("ALLL34", "Atlas Labs LLC", "Healthcare", "US", 20557.8, 24.7, 0.4, 4.4, 832.3),
    PublicComp("MDI35.NS", "Mahindra Data India", "Tech", "IND", 9524.4, 15.4, 0.38, 3.0, 618.5),
    PublicComp("NBG43", "Nova Brokers Group", "Equity Services", "US", 17278.4, 12.6, 0.48, 4.9, 1371.3),
    PublicComp("KKRT84", "KKR Tech Corp", "Tech", "US", 6254.5, 15.0, 0.46, 5.1, 417.0),
    PublicComp("NSLL27", "Nova Soft LLC", "Tech", "US", 25432.4, 18.9, 0.52, 5.6, 1345.6),
    PublicComp("TVSM35.NS", "TVS Motors Industries", "Industrials", "IND", 34002.0, 19.9, 0.45, 5.8, 1708.6),
    PublicComp("PEG75", "Pinnacle Equities Group", "Financials", "US", 15628.3, 10.9, 0.33, 1.3, 1433.8),
    PublicComp("BDLL45", "Blackstone Digital LLC", "Tech", "US", 16129.8, 13.4, 0.55, 1.4, 1203.7),
    PublicComp("KKRG69", "KKR Goods Group", "Consumer", "US", 30872.8, 13.8, 0.35, 5.0, 2237.2),
    PublicComp("BSL23.NS", "Bajaj Services Ltd", "Equity Services", "IND", 22704.1, 9.1, 0.23, 2.7, 2495.0),
    PublicComp("ALC81", "Apex Labs Corp", "Healthcare", "US", 48621.9, 17.8, 0.52, 3.4, 2731.6),
    PublicComp("CMC39", "Crest Motors Corp", "Industrials", "US", 32573.1, 21.8, 0.42, 1.5, 1494.2),
    PublicComp("AEL70.NS", "Adani Equities Ltd", "Financials", "IND", 32688.3, 14.3, 0.39, 5.0, 2285.9),
    PublicComp("BFI87", "Blackstone Fin Inc", "Financials", "US", 19448.5, 13.7, 0.34, 4.4, 1419.6),
    PublicComp("MGI33.NS", "Murugappa Group Industries", "Consumer", "IND", 45992.1, 22.2, 0.21, 3.6, 2071.7),
    PublicComp("SLI25", "Stellar Life Inc", "Healthcare", "US", 1563.0, 16.1, 0.2, 4.0, 97.1),
    PublicComp("MCE67.NS", "Mahindra Consumer Enterprises", "Consumer", "IND", 2256.8, 17.5, 0.5, 1.8, 129.0),
    PublicComp("JSWH94.NS", "JSW Holdings India", "Financials", "IND", 36559.4, 23.8, 0.38, 1.1, 1536.1),
    PublicComp("VTL92.NS", "Vedanta Trust Ltd", "Energy", "IND", 35403.7, 14.9, 0.32, 4.4, 2376.1),
    PublicComp("MAE42.NS", "Murugappa Apparel Enterprises", "Consumer", "IND", 49161.5, 23.5, 0.25, 1.2, 2092.0),
    PublicComp("ACL41.NS", "Adani Capital Ltd", "Energy", "IND", 25202.9, 12.3, 0.52, 3.3, 2049.0),
    PublicComp("ATH82", "Acme Tech Holdings", "Tech", "US", 4006.7, 19.7, 0.53, 3.5, 203.4),
    PublicComp("AAIG78", "Apollo AI Group", "Tech", "US", 16689.4, 6.9, 0.32, 1.6, 2418.8),
    PublicComp("MSI16.NS", "Murugappa Sys India", "Tech", "IND", 3890.7, 16.5, 0.3, 3.4, 235.8),
    PublicComp("CDG81", "Carlyle Dynamics Group", "Tech", "US", 34679.0, 23.2, 0.28, 4.6, 1494.8),
    PublicComp("BHLL58", "Blackstone Holdings LLC", "Financials", "US", 16985.3, 21.3, 0.32, 4.7, 797.4),
    PublicComp("CRI77", "Crest Ratings Inc", "Equity Services", "US", 36983.5, 22.1, 0.54, 4.5, 1673.5),
    PublicComp("BAIE90.NS", "Birla AI Enterprises", "Tech", "IND", 9012.5, 21.8, 0.52, 5.7, 413.4),
    PublicComp("CBC68", "Crest Bank Corp", "Energy", "US", 30312.4, 9.6, 0.3, 3.0, 3157.5),
    PublicComp("SMI74", "Stellar Mart Inc", "Consumer", "US", 48418.2, 8.3, 0.48, 1.5, 5833.5),
    PublicComp("AGLL38", "Apollo Global LLC", "Equity Services", "US", 5692.6, 24.4, 0.58, 2.4, 233.3),
    PublicComp("TBL40.NS", "Tata Bio Ltd", "Healthcare", "IND", 26099.1, 21.6, 0.46, 2.8, 1208.3),
    PublicComp("CDC22", "Crest Dynamics Corp", "Tech", "US", 11119.8, 16.1, 0.38, 4.5, 690.7),
    PublicComp("BML38.NS", "Birla Med Ltd", "Healthcare", "IND", 45589.1, 13.8, 0.26, 1.1, 3303.6),
    PublicComp("RFL88.NS", "Reliance Foods Ltd", "Consumer", "IND", 28118.2, 22.9, 0.53, 5.3, 1227.9),
    PublicComp("CPG74", "Carlyle Partners Group", "Energy", "US", 29750.8, 13.4, 0.52, 4.8, 2220.2),
    PublicComp("PRH53", "Pinnacle Ratings Holdings", "Equity Services", "US", 19020.1, 13.3, 0.25, 4.9, 1430.1),
    PublicComp("BMG78", "Blackstone Mart Group", "Consumer", "US", 43804.2, 6.9, 0.46, 4.0, 6348.4),
    PublicComp("GRI71.NS", "Godrej Retail Industries", "Consumer", "IND", 46570.4, 18.8, 0.44, 1.8, 2477.1),
    PublicComp("QPG59", "Quantum Partners Group", "Energy", "US", 34837.3, 22.8, 0.26, 1.3, 1528.0),
    PublicComp("KKRB54", "KKR Bank Holdings", "Energy", "US", 39715.3, 22.4, 0.56, 3.9, 1773.0),
    PublicComp("BGI77.NS", "Bajaj Global India", "Equity Services", "IND", 26673.1, 16.0, 0.43, 2.5, 1667.1),
    PublicComp("JSWW46.NS", "JSW Wealth Ltd", "Energy", "IND", 37826.1, 23.3, 0.33, 1.7, 1623.4),
    PublicComp("QGH97", "Quantum Genomics Holdings", "Healthcare", "US", 33064.6, 10.1, 0.59, 3.7, 3273.7),
    PublicComp("BAL14.NS", "Bajaj Analytics Ltd", "Equity Services", "IND", 4762.2, 21.8, 0.42, 2.1, 218.4),
    PublicComp("AME86.NS", "Adani Mfg Enterprises", "Industrials", "IND", 34260.7, 23.8, 0.45, 1.3, 1439.5),
    PublicComp("JPE91.NS", "Jindal Partners Enterprises", "Energy", "IND", 4212.3, 16.7, 0.56, 1.6, 252.2),
    PublicComp("RDI33.NS", "Reliance Dynamics Industries", "Tech", "IND", 28812.4, 21.6, 0.43, 5.4, 1333.9),
    PublicComp("API44.NS", "Adani Partners India", "Energy", "IND", 12753.9, 15.5, 0.45, 5.5, 822.8),
    PublicComp("JSWP24.NS", "JSW Partners India", "Financials", "IND", 25434.0, 21.3, 0.21, 2.2, 1194.1),
    PublicComp("VGG32", "Vertex Global Group", "Consumer", "US", 26087.7, 20.3, 0.32, 1.1, 1285.1),
    PublicComp("NHC54", "Nexus Heavy Corp", "Industrials", "US", 14233.6, 12.0, 0.41, 5.4, 1186.1),
    PublicComp("NELL42", "Nexus Equities LLC", "Financials", "US", 34972.5, 7.1, 0.27, 2.7, 4925.7),
    PublicComp("GMI99.NS", "Godrej Mfg India", "Industrials", "IND", 14358.3, 19.9, 0.3, 2.1, 721.5),
    PublicComp("AGH46", "Apex Global Holdings", "Consumer", "US", 37696.2, 7.6, 0.22, 2.1, 4960.0),
    PublicComp("RGI60.NS", "Reliance Global India", "Equity Services", "IND", 24940.9, 6.4, 0.45, 3.1, 3897.0),
    PublicComp("GDE10.NS", "Godrej Dynamics Enterprises", "Tech", "IND", 41513.2, 9.6, 0.27, 2.9, 4324.3),
    PublicComp("CCH96", "Carlyle Corp Holdings", "Industrials", "US", 21327.0, 21.3, 0.42, 2.7, 1001.3),
    PublicComp("RGL37.NS", "Reliance Global Ltd", "Equity Services", "IND", 22230.3, 7.3, 0.46, 3.0, 3045.2),
    PublicComp("AAG32", "Acme Asset Group", "Energy", "US", 33318.2, 25.0, 0.49, 1.3, 1332.7),
    PublicComp("NGI97", "Nexus Genomics Inc", "Healthcare", "US", 15457.1, 18.4, 0.28, 4.6, 840.1),
    PublicComp("GMRF33.NS", "GMR Fin Industries", "Financials", "IND", 9726.5, 10.7, 0.45, 1.7, 909.0),
    PublicComp("VFI27.NS", "Vedanta Foods Industries", "Consumer", "IND", 46924.4, 21.9, 0.57, 2.1, 2142.7),
    PublicComp("SFI67", "Stellar Fin Inc", "Financials", "US", 32106.9, 15.3, 0.41, 4.8, 2098.5),
    PublicComp("ACI65.NS", "Adani Cloud Industries", "Tech", "IND", 35164.7, 22.1, 0.4, 2.0, 1591.2),
    PublicComp("LTSI68.NS", "L&T Services Industries", "Equity Services", "IND", 39341.2, 20.3, 0.36, 2.1, 1938.0),
    PublicComp("GMI39.NS", "Godrej Markets Industries", "Equity Services", "IND", 37572.1, 17.4, 0.32, 2.1, 2159.3),
    PublicComp("JSWA69.NS", "JSW Aero Ltd", "Industrials", "IND", 48307.4, 6.8, 0.37, 5.2, 7104.0),
    PublicComp("NPC83", "Nexus Partners Corp", "Energy", "US", 41002.0, 10.0, 0.39, 3.7, 4100.2),
    PublicComp("JSWT84.NS", "JSW Trust Industries", "Energy", "IND", 7326.6, 24.2, 0.3, 4.2, 302.8),
    PublicComp("NMG86", "Nexus Markets Group", "Equity Services", "US", 9392.1, 15.7, 0.57, 5.6, 598.2),
    PublicComp("JSWR44.NS", "JSW Retail Industries", "Consumer", "IND", 26441.9, 13.3, 0.6, 4.3, 1988.1),
    PublicComp("MBL47.NS", "Mahindra Bank Ltd", "Energy", "IND", 1944.0, 24.7, 0.38, 4.5, 78.7),
    PublicComp("APL71.NS", "Adani Partners Ltd", "Financials", "IND", 8920.2, 23.3, 0.42, 5.0, 382.8),
    PublicComp("CCI30", "Crest Capital Inc", "Energy", "US", 13649.2, 15.0, 0.46, 3.5, 909.9),
    PublicComp("MRL53.NS", "Mahindra Ratings Ltd", "Equity Services", "IND", 22488.4, 19.0, 0.53, 4.8, 1183.6),
    PublicComp("CSH70", "Carlyle Steel Holdings", "Industrials", "US", 43906.5, 23.9, 0.43, 5.0, 1837.1),
    PublicComp("QSG66", "Quantum Soft Group", "Tech", "US", 8934.7, 23.7, 0.6, 5.7, 377.0),
    PublicComp("CLG12", "Crest Labs Group", "Healthcare", "US", 37641.7, 24.6, 0.24, 1.1, 1530.2),
    PublicComp("VHL89.NS", "Vedanta Health Ltd", "Healthcare", "IND", 23788.8, 14.9, 0.28, 3.4, 1596.6),
    PublicComp("KKRG80", "KKR Global Holdings", "Consumer", "US", 10047.4, 17.4, 0.25, 3.5, 577.4),
    PublicComp("QFC94", "Quantum Fin Corp", "Financials", "US", 4166.2, 11.6, 0.55, 2.2, 359.2),
    PublicComp("TTL83.NS", "Tata Trust Ltd", "Energy", "IND", 28503.0, 23.2, 0.48, 1.3, 1228.6),
    PublicComp("MBI57.NS", "Mahindra Build Industries", "Industrials", "IND", 33364.1, 24.1, 0.58, 2.1, 1384.4),
    PublicComp("GMRB76.NS", "GMR Brands India", "Consumer", "IND", 6594.9, 11.8, 0.22, 2.9, 558.9),
    PublicComp("PNG64", "Pinnacle Networks Group", "Tech", "US", 5888.2, 21.8, 0.22, 3.3, 270.1),
    PublicComp("JSWB39.NS", "JSW Brokers Enterprises", "Equity Services", "IND", 17171.3, 8.7, 0.29, 3.8, 1973.7),
    PublicComp("VBC73", "Vertex Build Corp", "Industrials", "US", 21619.0, 18.7, 0.38, 3.2, 1156.1),
    PublicComp("MCL75.NS", "Mahindra Capital Ltd", "Energy", "IND", 3238.1, 20.5, 0.51, 1.9, 158.0),
    PublicComp("VFE79.NS", "Vedanta Foods Enterprises", "Consumer", "IND", 29692.5, 9.1, 0.46, 4.3, 3262.9),
    PublicComp("JAL46.NS", "Jindal Apparel Ltd", "Consumer", "IND", 17008.1, 17.3, 0.41, 2.8, 983.1),
    PublicComp("RWI36.NS", "Reliance Wealth India", "Energy", "IND", 15996.2, 18.1, 0.5, 1.7, 883.8),
    PublicComp("MRI36.NS", "Murugappa Ratings India", "Equity Services", "IND", 29597.6, 16.0, 0.34, 1.4, 1849.8),
    PublicComp("BDL28.NS", "Birla Data Ltd", "Tech", "IND", 21625.5, 22.4, 0.44, 2.6, 965.4),
    PublicComp("CDH72", "Carlyle Digital Holdings", "Tech", "US", 26032.4, 16.9, 0.54, 5.4, 1540.4),
    PublicComp("VGG54", "Vertex Goods Group", "Consumer", "US", 48088.0, 16.7, 0.51, 1.3, 2879.5),
    PublicComp("MPL26.NS", "Murugappa Partners Ltd", "Energy", "IND", 35995.5, 6.0, 0.23, 1.4, 5999.2),
    PublicComp("VSI33.NS", "Vedanta Sys India", "Tech", "IND", 6819.6, 7.8, 0.34, 2.3, 874.3),
    PublicComp("BAIE71.NS", "Bajaj AI Enterprises", "Tech", "IND", 2590.8, 21.8, 0.22, 4.2, 118.8),
    PublicComp("VDH20", "Vertex Dynamics Holdings", "Tech", "US", 19142.3, 13.0, 0.44, 2.3, 1472.5),
    PublicComp("VHG59", "Vertex Health Group", "Healthcare", "US", 44702.1, 12.0, 0.44, 5.8, 3725.2),
    PublicComp("BCH82", "Blackstone Capital Holdings", "Financials", "US", 42747.2, 18.5, 0.34, 2.8, 2310.7),
    PublicComp("NDC83", "Nexus Data Corp", "Tech", "US", 35956.6, 9.4, 0.22, 4.0, 3825.2),
    PublicComp("RBI98.NS", "Reliance Bio Industries", "Healthcare", "IND", 9222.8, 11.9, 0.44, 4.0, 775.0),
    PublicComp("GMRH82.NS", "GMR Holdings Enterprises", "Energy", "IND", 40311.3, 17.2, 0.25, 3.8, 2343.7),
    PublicComp("CTH47", "Crest Trust Holdings", "Energy", "US", 44616.4, 10.9, 0.22, 1.7, 4093.2),
    PublicComp("BCI14.NS", "Bajaj Credit India", "Energy", "IND", 30334.7, 11.8, 0.53, 5.3, 2570.7),
    PublicComp("ATLL64", "Acme Thera LLC", "Healthcare", "US", 32827.3, 6.3, 0.47, 3.9, 5210.7),
    PublicComp("PTG18", "Pinnacle Trust Group", "Energy", "US", 47682.3, 8.6, 0.38, 1.7, 5544.5),
    PublicComp("GSI32.NS", "Godrej Soft Industries", "Tech", "IND", 18813.2, 20.2, 0.56, 1.9, 931.3),
    PublicComp("VSG56", "Vertex Soft Group", "Tech", "US", 14983.2, 24.4, 0.56, 3.0, 614.1),
    PublicComp("AMG35", "Acme Motors Group", "Industrials", "US", 30146.6, 23.8, 0.4, 1.9, 1266.7),
    PublicComp("MSI13.NS", "Mahindra Services India", "Equity Services", "IND", 4414.3, 6.2, 0.44, 3.1, 712.0),
    PublicComp("PHG98", "Pinnacle Holdings Group", "Financials", "US", 37667.2, 7.7, 0.28, 2.4, 4891.8),
    PublicComp("RBI74.NS", "Reliance Brands Industries", "Consumer", "IND", 7435.6, 23.5, 0.45, 5.2, 316.4),
    PublicComp("APH51", "Atlas Partners Holdings", "Financials", "US", 11269.8, 21.8, 0.43, 3.1, 517.0),
    PublicComp("CHH13", "Crest Health Holdings", "Healthcare", "US", 48118.7, 21.6, 0.4, 5.1, 2227.7),
    PublicComp("JGE38.NS", "Jindal Global Enterprises", "Consumer", "IND", 48174.9, 9.2, 0.27, 4.9, 5236.4),
    PublicComp("JGL30.NS", "Jindal Group Ltd", "Consumer", "IND", 9905.7, 24.2, 0.44, 6.0, 409.3),
    PublicComp("MFI42.NS", "Murugappa Foods India", "Consumer", "IND", 23176.0, 10.1, 0.43, 1.6, 2294.7),
    PublicComp("BELL58", "Blackstone Exchange LLC", "Equity Services", "US", 37370.3, 12.5, 0.46, 5.7, 2989.6),
    PublicComp("ALLL82", "Atlas Labs LLC", "Healthcare", "US", 26467.0, 19.1, 0.47, 4.1, 1385.7),
    PublicComp("GBI83.NS", "Godrej Build Industries", "Industrials", "IND", 44563.7, 7.8, 0.43, 1.9, 5713.3),
    PublicComp("JCI96.NS", "Jindal Credit India", "Financials", "IND", 19239.2, 14.0, 0.33, 3.8, 1374.2),
    PublicComp("MFI93.NS", "Mahindra Fin India", "Energy", "IND", 10906.4, 24.1, 0.49, 2.7, 452.5),
    PublicComp("GMRL53.NS", "GMR Life Ltd", "Healthcare", "IND", 28391.7, 9.7, 0.24, 5.1, 2927.0),
    PublicComp("LTBE60.NS", "L&T Brokers Enterprises", "Equity Services", "IND", 32115.6, 17.3, 0.21, 3.6, 1856.4),
    PublicComp("ACLL91", "Apollo Credit LLC", "Financials", "US", 38862.3, 11.2, 0.26, 4.9, 3469.8),
    PublicComp("MAI63.NS", "Mahindra Analytics Industries", "Equity Services", "IND", 43750.3, 11.9, 0.43, 2.7, 3676.5),
    PublicComp("JSWT20.NS", "JSW Trust India", "Financials", "IND", 29875.3, 15.5, 0.53, 4.7, 1927.4),
    PublicComp("JSL55.NS", "Jindal Sys Ltd", "Tech", "IND", 34455.5, 15.0, 0.31, 4.5, 2297.0),
    PublicComp("KKRG52", "KKR Group LLC", "Consumer", "US", 33625.2, 10.3, 0.54, 3.9, 3264.6),
    PublicComp("MBI42.NS", "Murugappa Brands Industries", "Consumer", "IND", 40554.8, 11.6, 0.49, 1.1, 3496.1),
    PublicComp("KKRM73", "KKR Mart Inc", "Consumer", "US", 9999.3, 12.2, 0.54, 4.2, 819.6),
    PublicComp("MCI19.NS", "Murugappa Credit Industries", "Energy", "IND", 21771.6, 23.1, 0.47, 5.4, 942.5),
    PublicComp("ALL77.NS", "Adani Labs Ltd", "Healthcare", "IND", 25145.5, 18.8, 0.53, 1.2, 1337.5),
    PublicComp("NSI80", "Nexus Services Inc", "Equity Services", "US", 15093.5, 9.6, 0.26, 5.5, 1572.2),
    PublicComp("ARG86", "Atlas Ratings Group", "Equity Services", "US", 8022.5, 10.1, 0.35, 2.2, 794.3),
    PublicComp("GMRE66.NS", "GMR Exchange Enterprises", "Equity Services", "IND", 14212.3, 20.5, 0.58, 4.7, 693.3),
    PublicComp("QPH30", "Quantum Pharma Holdings", "Healthcare", "US", 5997.8, 12.0, 0.47, 2.0, 499.8),
    PublicComp("SLH62", "Stellar Labs Holdings", "Healthcare", "US", 24526.6, 17.6, 0.59, 5.4, 1393.6),
    PublicComp("NEC47", "Nexus Equities Corp", "Financials", "US", 21424.6, 6.0, 0.26, 2.2, 3570.8),
    PublicComp("ADC83", "Apex Dynamics Corp", "Tech", "US", 10015.6, 23.3, 0.59, 2.0, 429.9),
    PublicComp("TVSS26.NS", "TVS Sys India", "Tech", "IND", 48412.4, 23.3, 0.29, 4.9, 2077.8),
    PublicComp("SHI65", "Stellar Health Inc", "Healthcare", "US", 22782.0, 7.7, 0.25, 4.8, 2958.7),
    PublicComp("TPI37.NS", "Tata Partners Industries", "Financials", "IND", 35982.4, 15.8, 0.5, 2.3, 2277.4),
    PublicComp("CBG13", "Carlyle Brands Group", "Consumer", "US", 45845.4, 11.1, 0.34, 2.3, 4130.2),
    PublicComp("NTLL29", "Nova Tech LLC", "Tech", "US", 46800.4, 9.6, 0.35, 4.3, 4875.0),
    PublicComp("AAIH75", "Apex AI Holdings", "Tech", "US", 35634.3, 7.4, 0.36, 3.9, 4815.4),
    PublicComp("RME67.NS", "Reliance Motors Enterprises", "Industrials", "IND", 15339.2, 14.0, 0.56, 2.6, 1095.7),
    PublicComp("VLC90", "Vanguard Labs Corp", "Healthcare", "US", 36305.6, 14.9, 0.43, 3.5, 2436.6),
    PublicComp("ABC73", "Atlas Bio Corp", "Healthcare", "US", 15833.3, 11.5, 0.49, 2.1, 1376.8),
    PublicComp("GRI91.NS", "Godrej Ratings Industries", "Equity Services", "IND", 42694.2, 22.7, 0.56, 2.0, 1880.8),
    PublicComp("ABH33", "Acme Brands Holdings", "Consumer", "US", 12586.3, 24.5, 0.32, 1.6, 513.7),
    PublicComp("BEI31.NS", "Bajaj Equities Industries", "Energy", "IND", 33716.3, 23.5, 0.23, 1.7, 1434.7),
    PublicComp("TFI39.NS", "Tata Fin Industries", "Energy", "IND", 29265.8, 17.2, 0.49, 4.4, 1701.5),
    PublicComp("NNI74", "Nexus Networks Inc", "Tech", "US", 15464.4, 14.5, 0.41, 1.5, 1066.5),
    PublicComp("BCE46.NS", "Bajaj Cloud Enterprises", "Tech", "IND", 21830.5, 13.1, 0.53, 3.8, 1666.5),
    PublicComp("CDLL98", "Crest Data LLC", "Tech", "US", 28919.5, 21.9, 0.52, 3.4, 1320.5),
    PublicComp("BRE95.NS", "Birla Retail Enterprises", "Consumer", "IND", 29635.1, 24.4, 0.29, 5.3, 1214.6),
    PublicComp("BDC80", "Blackstone Digital Corp", "Tech", "US", 36331.3, 22.3, 0.25, 5.2, 1629.2),
    PublicComp("GGI29.NS", "Godrej Global Industries", "Consumer", "IND", 33522.8, 22.7, 0.27, 3.9, 1476.8),
    PublicComp("CTLL61", "Crest Trust LLC", "Financials", "US", 16648.1, 11.3, 0.35, 2.5, 1473.3),
    PublicComp("VRLL12", "Vanguard Ratings LLC", "Equity Services", "US", 44847.3, 8.8, 0.22, 3.0, 5096.3),
    PublicComp("PAH18", "Pinnacle Asset Holdings", "Financials", "US", 20388.0, 16.6, 0.3, 4.8, 1228.2),
    PublicComp("BCI36.NS", "Bajaj Credit Industries", "Financials", "IND", 24053.7, 8.8, 0.48, 4.5, 2733.4),
    PublicComp("PAH13", "Pinnacle Asset Holdings", "Financials", "US", 24437.2, 11.3, 0.39, 1.1, 2162.6),
    PublicComp("SDG44", "Stellar Data Group", "Tech", "US", 36221.9, 11.5, 0.47, 3.3, 3149.7),
    PublicComp("BWH64", "Blackstone Wealth Holdings", "Financials", "US", 22887.5, 11.0, 0.51, 4.2, 2080.7),
    PublicComp("CMH31", "Carlyle Mfg Holdings", "Industrials", "US", 40927.9, 18.4, 0.55, 3.5, 2224.3),
    PublicComp("VLH27", "Vertex Life Holdings", "Healthcare", "US", 26425.5, 14.1, 0.35, 3.3, 1874.1),
    PublicComp("LTNI97.NS", "L&T Networks India", "Tech", "IND", 1489.3, 12.2, 0.52, 1.5, 122.1),
    PublicComp("NDH96", "Nexus Data Holdings", "Tech", "US", 29742.6, 15.3, 0.4, 4.5, 1944.0),
    PublicComp("JSWP61.NS", "JSW Partners India", "Financials", "IND", 49329.3, 14.2, 0.54, 3.9, 3473.9),
    PublicComp("VLH47", "Vertex Life Holdings", "Healthcare", "US", 3402.8, 17.3, 0.53, 3.0, 196.7),
    PublicComp("PCG31", "Pinnacle Corp Group", "Industrials", "US", 39641.8, 14.4, 0.3, 3.2, 2752.9),
    PublicComp("AIC25", "Acme Infra Corp", "Industrials", "US", 37917.6, 21.5, 0.31, 1.5, 1763.6),
    PublicComp("JFI26.NS", "Jindal Fin India", "Financials", "IND", 25553.7, 24.9, 0.52, 3.1, 1026.3),
    PublicComp("VCC40", "Vertex Capital Corp", "Energy", "US", 19596.6, 11.9, 0.47, 1.9, 1646.8),
    PublicComp("MCI10.NS", "Murugappa Cyber India", "Tech", "IND", 49755.8, 13.9, 0.28, 5.4, 3579.6),
    PublicComp("ASLL92", "Apex Sys LLC", "Tech", "US", 49322.2, 20.7, 0.27, 2.3, 2382.7),
    PublicComp("LTAI53.NS", "L&T Apparel Industries", "Consumer", "IND", 11969.0, 18.6, 0.59, 3.1, 643.5),
    PublicComp("BGL59.NS", "Bajaj Global Ltd", "Equity Services", "IND", 35557.9, 24.0, 0.26, 4.5, 1481.6),
    PublicComp("CGC80", "Crest Goods Corp", "Consumer", "US", 46140.4, 16.2, 0.32, 1.9, 2848.2),
    PublicComp("MML81.NS", "Mahindra Markets Ltd", "Equity Services", "IND", 29104.0, 14.5, 0.57, 1.4, 2007.2),
    PublicComp("CGI98", "Crest Goods Inc", "Consumer", "US", 23081.7, 23.9, 0.48, 1.8, 965.8),
    PublicComp("VTI56.NS", "Vedanta Trust India", "Energy", "IND", 24421.5, 10.3, 0.27, 4.7, 2371.0),
    PublicComp("VHG76", "Vanguard Heavy Group", "Industrials", "US", 31811.5, 24.7, 0.37, 2.7, 1287.9),
    PublicComp("STLL29", "Stellar Tech LLC", "Tech", "US", 14467.4, 12.2, 0.48, 5.7, 1185.9),
    PublicComp("TRI20.NS", "Tata Ratings Industries", "Equity Services", "IND", 38224.0, 17.7, 0.23, 4.9, 2159.5),
    PublicComp("AFI73.NS", "Adani Fin India", "Financials", "IND", 16215.2, 23.6, 0.23, 1.4, 687.1),
    PublicComp("AGI96", "Apollo Genomics Inc", "Healthcare", "US", 36356.6, 23.2, 0.35, 3.3, 1567.1),
    PublicComp("JSWM18.NS", "JSW Markets Ltd", "Equity Services", "IND", 22519.0, 19.4, 0.54, 5.1, 1160.8),
    PublicComp("ABL98.NS", "Adani Bank Ltd", "Energy", "IND", 14330.6, 7.0, 0.38, 4.0, 2047.2),
    PublicComp("ACH81", "Acme Capital Holdings", "Energy", "US", 24786.0, 6.8, 0.54, 4.1, 3645.0),
    PublicComp("AAI78.NS", "Adani Aero Industries", "Industrials", "IND", 33679.5, 13.1, 0.21, 6.0, 2571.0),
    PublicComp("BNL11.NS", "Bajaj Networks Ltd", "Tech", "IND", 49399.6, 22.5, 0.24, 4.4, 2195.5),
    PublicComp("VFG74", "Vertex Foods Group", "Consumer", "US", 27969.7, 21.2, 0.58, 4.2, 1319.3),
    PublicComp("QNI74", "Quantum Networks Inc", "Tech", "US", 30833.9, 17.5, 0.58, 1.2, 1761.9),
    PublicComp("BHI50.NS", "Bajaj Heavy India", "Industrials", "IND", 27187.7, 17.0, 0.31, 1.2, 1599.3),
    PublicComp("CBG41", "Crest Bank Group", "Financials", "US", 10301.3, 9.1, 0.26, 4.7, 1132.0),
    PublicComp("BSI45.NS", "Birla Services Industries", "Equity Services", "IND", 3145.4, 18.6, 0.25, 3.9, 169.1),
    PublicComp("AGL21.NS", "Adani Group Ltd", "Consumer", "IND", 39364.1, 12.7, 0.34, 4.9, 3099.5),
    PublicComp("CTH39", "Carlyle Trust Holdings", "Energy", "US", 21958.8, 23.0, 0.37, 3.7, 954.7),
    PublicComp("BME89.NS", "Birla Motors Enterprises", "Industrials", "IND", 27709.0, 22.8, 0.36, 2.6, 1215.3),
    PublicComp("JSWM26.NS", "JSW Mfg Industries", "Industrials", "IND", 38099.9, 8.5, 0.56, 5.7, 4482.3),
    PublicComp("MCE90.NS", "Mahindra Consumer Enterprises", "Consumer", "IND", 15191.3, 23.0, 0.36, 1.2, 660.5),
    PublicComp("PHH89", "Pinnacle Holdings Holdings", "Financials", "US", 36023.1, 9.1, 0.33, 2.2, 3958.6),
    PublicComp("AELL88", "Acme Equities LLC", "Financials", "US", 33414.0, 21.8, 0.56, 5.2, 1532.8),
    PublicComp("BAE69.NS", "Birla Analytics Enterprises", "Equity Services", "IND", 24058.4, 6.1, 0.55, 4.1, 3944.0),
    PublicComp("APH47", "Apex Partners Holdings", "Energy", "US", 42713.8, 14.5, 0.45, 1.5, 2945.8),
    PublicComp("KKRC93", "KKR Capital Corp", "Energy", "US", 21655.0, 6.3, 0.39, 3.6, 3437.3),
    PublicComp("AIC44", "Apollo Industrial Corp", "Industrials", "US", 12472.3, 22.7, 0.35, 5.6, 549.4),
    PublicComp("VAIG26", "Vanguard AI Group", "Tech", "US", 37893.5, 12.1, 0.38, 2.3, 3131.7),
    PublicComp("AEI75", "Apollo Engineering Inc", "Industrials", "US", 11991.3, 24.4, 0.45, 3.5, 491.4),
    PublicComp("MBI64.NS", "Mahindra Bio India", "Healthcare", "IND", 12144.4, 23.2, 0.21, 2.4, 523.5),
    PublicComp("VPC97", "Vertex Pharma Corp", "Healthcare", "US", 35865.2, 22.6, 0.23, 1.1, 1587.0),
    PublicComp("BAI88.NS", "Bajaj Aero Industries", "Industrials", "IND", 8611.6, 15.1, 0.59, 2.3, 570.3),
    PublicComp("QPG26", "Quantum Partners Group", "Financials", "US", 35043.9, 21.4, 0.31, 3.7, 1637.6),
    PublicComp("NBH15", "Nova Brokers Holdings", "Equity Services", "US", 37763.7, 7.1, 0.56, 5.2, 5318.8),
    PublicComp("ACI69.NS", "Adani Capital Industries", "Energy", "IND", 31162.0, 14.4, 0.39, 5.9, 2164.0),
    PublicComp("VMC42", "Vanguard Markets Corp", "Equity Services", "US", 36421.0, 18.9, 0.27, 2.3, 1927.0),
    PublicComp("VCI35", "Vertex Capital Inc", "Financials", "US", 25703.2, 6.9, 0.36, 1.3, 3725.1),
    PublicComp("SDG59", "Stellar Diagnostics Group", "Healthcare", "US", 7587.7, 20.3, 0.37, 2.6, 373.8),
    PublicComp("JSWI31.NS", "JSW Industrial Enterprises", "Industrials", "IND", 29572.9, 24.3, 0.58, 5.7, 1217.0),
    PublicComp("BMH36", "Blackstone Med Holdings", "Healthcare", "US", 28545.9, 24.5, 0.29, 3.4, 1165.1),
    PublicComp("ABG13", "Atlas Bank Group", "Energy", "US", 1081.0, 10.9, 0.37, 5.8, 99.2),
    PublicComp("SFH83", "Stellar Fin Holdings", "Energy", "US", 44946.0, 22.6, 0.23, 4.2, 1988.8),
    PublicComp("QSG68", "Quantum Sys Group", "Tech", "US", 45998.8, 19.1, 0.33, 2.5, 2408.3),
    PublicComp("VRG45", "Vanguard Ratings Group", "Equity Services", "US", 26502.5, 23.7, 0.39, 5.6, 1118.2),
    PublicComp("GMRM20.NS", "GMR Med Enterprises", "Healthcare", "IND", 8447.2, 20.4, 0.5, 3.5, 414.1),
    PublicComp("RBE51.NS", "Reliance Bank Enterprises", "Financials", "IND", 23644.0, 12.7, 0.44, 5.9, 1861.7),
    PublicComp("BSI35.NS", "Birla Services India", "Equity Services", "IND", 37245.2, 20.3, 0.21, 1.1, 1834.7),
    PublicComp("VTI40.NS", "Vedanta Tech India", "Tech", "IND", 18021.1, 20.7, 0.33, 5.6, 870.6),
    PublicComp("NMH91", "Nova Mfg Holdings", "Industrials", "US", 6059.3, 20.2, 0.34, 1.4, 300.0),
    PublicComp("GDE82.NS", "Godrej Data Enterprises", "Tech", "IND", 24849.9, 6.1, 0.4, 1.8, 4073.8),
    PublicComp("VBC89", "Vertex Build Corp", "Industrials", "US", 1049.7, 19.2, 0.23, 4.9, 54.7),
    PublicComp("VEC80", "Vertex Engineering Corp", "Industrials", "US", 40592.1, 10.7, 0.45, 5.1, 3793.7),
    PublicComp("NEC27", "Nexus Exchange Corp", "Equity Services", "US", 28277.8, 20.9, 0.31, 3.3, 1353.0),
    PublicComp("TVSG97.NS", "TVS Group Ltd", "Consumer", "IND", 28484.7, 24.2, 0.46, 2.0, 1177.1),
    PublicComp("LTSI78.NS", "L&T Services India", "Equity Services", "IND", 3113.7, 6.9, 0.2, 5.4, 451.3),
    PublicComp("VLI11", "Vertex Life Inc", "Healthcare", "US", 48959.9, 9.8, 0.26, 5.5, 4995.9),
    PublicComp("QEC36", "Quantum Engineering Corp", "Industrials", "US", 40154.0, 12.3, 0.58, 3.5, 3264.6),
    PublicComp("AWL96.NS", "Adani Wealth Ltd", "Financials", "IND", 22098.1, 17.4, 0.25, 3.7, 1270.0),
    PublicComp("KKRM60", "KKR Mart Holdings", "Consumer", "US", 43856.2, 20.2, 0.35, 4.7, 2171.1),
    PublicComp("SRLL99", "Stellar Retail LLC", "Consumer", "US", 16166.5, 23.4, 0.41, 3.3, 690.9),
    PublicComp("TEI57.NS", "Tata Engineering Industries", "Industrials", "IND", 2605.5, 8.2, 0.26, 2.1, 317.7),
    PublicComp("PRLL15", "Pinnacle Retail LLC", "Consumer", "US", 1673.2, 11.8, 0.55, 1.3, 141.8),
    PublicComp("VAIG61", "Vertex AI Group", "Tech", "US", 12832.5, 18.5, 0.46, 3.4, 693.6),
    PublicComp("TVST71.NS", "TVS Tech Industries", "Tech", "IND", 8121.1, 13.8, 0.44, 2.2, 588.5),
    PublicComp("PBI34", "Pinnacle Bio Inc", "Healthcare", "US", 26734.3, 7.5, 0.34, 4.6, 3564.6),
    PublicComp("AGG72", "Apollo Goods Group", "Consumer", "US", 21595.1, 21.3, 0.36, 1.9, 1013.9),
    PublicComp("LTSL78.NS", "L&T Soft Ltd", "Tech", "IND", 20251.7, 17.5, 0.43, 4.6, 1157.2),
    PublicComp("ABG17", "Acme Brokers Group", "Equity Services", "US", 34888.5, 18.8, 0.29, 6.0, 1855.8),
    PublicComp("BBE96.NS", "Bajaj Brokers Enterprises", "Equity Services", "IND", 47182.5, 9.8, 0.21, 4.0, 4814.5),
    PublicComp("ATC20", "Atlas Tech Corp", "Tech", "US", 22280.4, 20.9, 0.45, 1.2, 1066.0),
    PublicComp("SEI61", "Stellar Exchange Inc", "Equity Services", "US", 6723.6, 16.2, 0.57, 5.4, 415.0),
    PublicComp("AMC90", "Apex Mart Corp", "Consumer", "US", 15682.4, 9.2, 0.33, 2.4, 1704.6),
    PublicComp("VPI54.NS", "Vedanta Partners Industries", "Energy", "IND", 41689.0, 6.1, 0.57, 3.8, 6834.3),
    PublicComp("LTAI85.NS", "L&T Asset India", "Financials", "IND", 3967.8, 17.4, 0.54, 2.2, 228.0),
    PublicComp("CSLL56", "Crest Sys LLC", "Tech", "US", 35254.8, 11.3, 0.33, 5.6, 3119.9),
    PublicComp("VLI93.NS", "Vedanta Lifestyle India", "Consumer", "IND", 32558.0, 22.0, 0.53, 2.9, 1479.9),
    PublicComp("MPI57.NS", "Mahindra Pharma India", "Healthcare", "IND", 27842.4, 20.9, 0.2, 1.9, 1332.2),
    PublicComp("AAH12", "Apex Analytics Holdings", "Equity Services", "US", 12222.6, 23.1, 0.25, 5.1, 529.1),
    PublicComp("BTL68.NS", "Bajaj Thera Ltd", "Healthcare", "IND", 49945.1, 17.6, 0.24, 1.4, 2837.8),
    PublicComp("TVST51.NS", "TVS Tech India", "Tech", "IND", 5014.4, 18.4, 0.24, 4.9, 272.5),
    PublicComp("VAC34", "Vertex Aero Corp", "Industrials", "US", 19769.2, 12.9, 0.39, 3.4, 1532.5),
    PublicComp("TVSH68.NS", "TVS Holdings Industries", "Energy", "IND", 23491.0, 11.2, 0.53, 2.9, 2097.4),
    PublicComp("GMI30.NS", "Godrej Markets Industries", "Equity Services", "IND", 48531.1, 20.9, 0.25, 2.3, 2322.1),
    PublicComp("VGI43.NS", "Vedanta Goods Industries", "Consumer", "IND", 15765.0, 14.4, 0.25, 4.0, 1094.8),
    PublicComp("QRH85", "Quantum Ratings Holdings", "Equity Services", "US", 37137.9, 6.3, 0.28, 2.7, 5894.9),
    PublicComp("GAL66.NS", "Godrej Apparel Ltd", "Consumer", "IND", 47924.7, 15.3, 0.47, 3.7, 3132.3),
    PublicComp("GTE98.NS", "Godrej Trust Enterprises", "Financials", "IND", 43959.3, 11.3, 0.38, 2.4, 3890.2),
    PublicComp("BAI52", "Blackstone Asset Inc", "Energy", "US", 10160.2, 11.0, 0.57, 5.3, 923.7),
    PublicComp("SFG14", "Stellar Fin Group", "Financials", "US", 42015.0, 19.0, 0.53, 4.8, 2211.3),
    PublicComp("GMI18.NS", "Godrej Markets Industries", "Equity Services", "IND", 7464.4, 24.3, 0.23, 4.1, 307.2),
    PublicComp("GMRC15.NS", "GMR Cyber India", "Tech", "IND", 23233.1, 24.9, 0.57, 3.9, 933.1),
    PublicComp("CGI42", "Crest Genomics Inc", "Healthcare", "US", 29365.3, 14.1, 0.35, 5.6, 2082.6),
    PublicComp("MIL84.NS", "Murugappa Infra Ltd", "Industrials", "IND", 24325.9, 16.3, 0.47, 2.3, 1492.4),
    PublicComp("QFG94", "Quantum Fin Group", "Financials", "US", 2729.3, 15.9, 0.44, 5.9, 171.7),
    PublicComp("AML68.NS", "Adani Med Ltd", "Healthcare", "IND", 13673.2, 12.8, 0.53, 4.8, 1068.2),
    PublicComp("ATL60.NS", "Adani Thera Ltd", "Healthcare", "IND", 10735.1, 9.6, 0.34, 2.3, 1118.2),
    PublicComp("TVSI96.NS", "TVS Infra Ltd", "Industrials", "IND", 13263.3, 19.3, 0.21, 5.9, 687.2),
    PublicComp("APLL35", "Atlas Partners LLC", "Energy", "US", 42535.5, 11.4, 0.46, 1.9, 3731.2),
    PublicComp("AEC40", "Apex Exchange Corp", "Equity Services", "US", 17980.6, 20.7, 0.38, 1.8, 868.6),
    PublicComp("JSWF29.NS", "JSW Foods Ltd", "Consumer", "IND", 29040.3, 21.0, 0.43, 5.3, 1382.9),
    PublicComp("BCC22", "Blackstone Consumer Corp", "Consumer", "US", 1099.6, 6.9, 0.52, 2.5, 159.4),
    PublicComp("NAC24", "Nexus Asset Corp", "Financials", "US", 5952.3, 21.7, 0.27, 5.2, 274.3),
    PublicComp("MCI68.NS", "Mahindra Care India", "Healthcare", "IND", 37540.9, 17.1, 0.28, 5.2, 2195.4),
    PublicComp("CGC65", "Crest Global Corp", "Consumer", "US", 37242.6, 8.8, 0.49, 1.7, 4232.1),
    PublicComp("MRE23.NS", "Murugappa Ratings Enterprises", "Equity Services", "IND", 28958.5, 8.4, 0.56, 4.5, 3447.4),
    PublicComp("VFL19.NS", "Vedanta Fin Ltd", "Energy", "IND", 15492.2, 9.8, 0.24, 1.7, 1580.8),
    PublicComp("JWI66.NS", "Jindal Wealth Industries", "Energy", "IND", 9143.9, 19.1, 0.58, 1.8, 478.7),
    PublicComp("NSG16", "Nova Services Group", "Equity Services", "US", 18128.1, 23.1, 0.42, 2.3, 784.8),
    PublicComp("AGH15", "Apollo Global Holdings", "Equity Services", "US", 23357.4, 9.1, 0.47, 5.8, 2566.7),
    PublicComp("SGG20", "Stellar Global Group", "Consumer", "US", 30679.8, 6.8, 0.31, 2.7, 4511.7),
    PublicComp("MCE85.NS", "Mahindra Care Enterprises", "Healthcare", "IND", 36822.7, 24.4, 0.24, 5.3, 1509.1),
    PublicComp("RDL87.NS", "Reliance Digital Ltd", "Tech", "IND", 31616.5, 6.1, 0.37, 5.5, 5183.0),
    PublicComp("GHI92.NS", "Godrej Holdings India", "Energy", "IND", 22659.7, 22.4, 0.36, 3.8, 1011.6),
    PublicComp("AFC90", "Apollo Fin Corp", "Financials", "US", 49587.1, 10.5, 0.6, 4.8, 4722.6),
    PublicComp("BCI85", "Blackstone Cyber Inc", "Tech", "US", 18511.6, 16.5, 0.43, 4.9, 1121.9),
    PublicComp("BBH69", "Blackstone Bank Holdings", "Financials", "US", 44534.5, 15.1, 0.36, 3.3, 2949.3),
    PublicComp("GMRB51.NS", "GMR Bank Industries", "Energy", "IND", 26698.8, 9.3, 0.33, 2.4, 2870.8),
    PublicComp("ADH30", "Apex Data Holdings", "Tech", "US", 42530.1, 17.5, 0.33, 2.5, 2430.3),
    PublicComp("CGC88", "Crest Goods Corp", "Consumer", "US", 31530.4, 13.5, 0.59, 5.9, 2335.6),
    PublicComp("BGI88", "Blackstone Global Inc", "Equity Services", "US", 4756.7, 17.9, 0.46, 5.5, 265.7),
    PublicComp("SFC88", "Stellar Foods Corp", "Consumer", "US", 27546.5, 14.5, 0.26, 4.5, 1899.8),
    PublicComp("ABI28.NS", "Adani Brokers India", "Equity Services", "IND", 47664.5, 8.8, 0.24, 3.0, 5416.4),
    PublicComp("BFC61", "Blackstone Foods Corp", "Consumer", "US", 30422.8, 16.0, 0.47, 4.9, 1901.4),
    PublicComp("RLI50.NS", "Reliance Lifestyle Industries", "Consumer", "IND", 23815.8, 15.6, 0.3, 2.0, 1526.7),
    PublicComp("VME63.NS", "Vedanta Motors Enterprises", "Industrials", "IND", 16568.3, 14.2, 0.48, 1.7, 1166.8),
    PublicComp("MFI15.NS", "Murugappa Fin India", "Financials", "IND", 8815.5, 9.3, 0.45, 4.6, 947.9),
    PublicComp("LTCE73.NS", "L&T Corp Enterprises", "Industrials", "IND", 39681.1, 8.1, 0.58, 2.6, 4898.9),
    PublicComp("TCL19.NS", "Tata Care Ltd", "Healthcare", "IND", 25015.1, 23.6, 0.44, 2.1, 1060.0),
    PublicComp("ABG21", "Atlas Brokers Group", "Equity Services", "US", 3261.0, 22.2, 0.29, 4.2, 146.9),
    PublicComp("BEL55.NS", "Birla Engineering Ltd", "Industrials", "IND", 18605.0, 6.2, 0.54, 4.1, 3000.8),
    PublicComp("KKRE46", "KKR Engineering Inc", "Industrials", "US", 21016.0, 20.9, 0.52, 4.4, 1005.6),
    PublicComp("NRH58", "Nova Ratings Holdings", "Equity Services", "US", 19839.5, 20.2, 0.49, 4.0, 982.2),
    PublicComp("CSLL60", "Crest Services LLC", "Equity Services", "US", 46273.7, 22.1, 0.31, 4.1, 2093.8),
    PublicComp("JLI97.NS", "Jindal Labs India", "Healthcare", "IND", 38005.2, 24.1, 0.36, 1.5, 1577.0),
    PublicComp("NTH25", "Nexus Tech Holdings", "Tech", "US", 47057.4, 20.3, 0.35, 1.9, 2318.1),
    PublicComp("SCLL51", "Stellar Capital LLC", "Financials", "US", 34472.5, 24.0, 0.51, 4.8, 1436.4),
    PublicComp("BBC81", "Blackstone Bank Corp", "Energy", "US", 16330.5, 21.6, 0.27, 5.0, 756.0),
    PublicComp("CWLL45", "Crest Wealth LLC", "Energy", "US", 16166.6, 15.1, 0.32, 3.4, 1070.6),
    PublicComp("JSWA40.NS", "JSW AI Enterprises", "Tech", "IND", 13592.8, 9.4, 0.41, 1.7, 1446.0),
    PublicComp("BCG22", "Blackstone Capital Group", "Energy", "US", 15554.5, 21.8, 0.52, 3.4, 713.5),
    PublicComp("CEC19", "Carlyle Equities Corp", "Energy", "US", 31873.7, 12.4, 0.36, 3.6, 2570.5),
    PublicComp("PDI13", "Pinnacle Data Inc", "Tech", "US", 47162.9, 6.7, 0.45, 1.2, 7039.2),
    PublicComp("VAH58", "Vertex Asset Holdings", "Energy", "US", 3516.6, 11.9, 0.45, 3.7, 295.5),
    PublicComp("ARG16", "Acme Retail Group", "Consumer", "US", 24855.0, 6.6, 0.31, 5.8, 3765.9),
    PublicComp("PBI87", "Pinnacle Build Inc", "Industrials", "US", 41575.6, 6.9, 0.24, 4.3, 6025.4),
    PublicComp("LTCE93.NS", "L&T Capital Enterprises", "Energy", "IND", 9021.5, 22.4, 0.34, 5.0, 402.7),
    PublicComp("JEI10.NS", "Jindal Exchange Industries", "Equity Services", "IND", 35531.4, 14.1, 0.56, 3.9, 2520.0),
    PublicComp("TVSD48.NS", "TVS Dynamics Enterprises", "Tech", "IND", 6597.4, 13.4, 0.23, 3.3, 492.3),
    PublicComp("QBG65", "Quantum Brokers Group", "Equity Services", "US", 23522.7, 24.5, 0.33, 5.4, 960.1),
    PublicComp("KKRB77", "KKR Bank Inc", "Energy", "US", 30043.9, 16.7, 0.56, 4.7, 1799.0),
    PublicComp("LTCI46.NS", "L&T Cyber Industries", "Tech", "IND", 3224.0, 22.0, 0.56, 5.7, 146.5),
    PublicComp("TVSB82.NS", "TVS Bio Industries", "Healthcare", "IND", 41681.4, 18.2, 0.47, 3.2, 2290.2),
    PublicComp("BDG93", "Blackstone Digital Group", "Tech", "US", 5472.5, 11.0, 0.25, 4.1, 497.5),
    PublicComp("AILL86", "Acme Infra LLC", "Industrials", "US", 47182.7, 14.3, 0.44, 3.1, 3299.5),
    PublicComp("VML45.NS", "Vedanta Mart Ltd", "Consumer", "IND", 2023.4, 23.5, 0.24, 5.5, 86.1),
    PublicComp("LTEE63.NS", "L&T Exchange Enterprises", "Equity Services", "IND", 13599.7, 20.4, 0.32, 2.0, 666.7),
    PublicComp("JSWL85.NS", "JSW Lifestyle India", "Consumer", "IND", 25270.3, 20.7, 0.55, 4.1, 1220.8),
    PublicComp("SILL52", "Stellar Industrial LLC", "Industrials", "US", 11969.6, 24.2, 0.33, 5.2, 494.6),
    PublicComp("MRE81.NS", "Mahindra Retail Enterprises", "Consumer", "IND", 48155.0, 22.1, 0.38, 3.6, 2179.0),
    PublicComp("VCL84.NS", "Vedanta Corp Ltd", "Industrials", "IND", 40131.5, 17.8, 0.35, 3.7, 2254.6),
    PublicComp("MME12.NS", "Murugappa Mart Enterprises", "Consumer", "IND", 34929.4, 15.3, 0.24, 2.5, 2283.0),
    PublicComp("BDLL62", "Blackstone Dynamics LLC", "Tech", "US", 12810.0, 17.3, 0.58, 2.9, 740.5),
    PublicComp("CBLL72", "Crest Bank LLC", "Energy", "US", 47663.0, 16.4, 0.48, 4.9, 2906.3),
    PublicComp("JSWT85.NS", "JSW Thera India", "Healthcare", "IND", 20600.1, 16.4, 0.55, 2.9, 1256.1),
    PublicComp("JSWD21.NS", "JSW Dynamics Industries", "Tech", "IND", 46560.3, 24.3, 0.28, 5.5, 1916.1),
    PublicComp("KKRH56", "KKR Heavy LLC", "Industrials", "US", 29746.0, 23.7, 0.52, 5.6, 1255.1),
    PublicComp("AEH59", "Acme Equities Holdings", "Financials", "US", 24920.7, 20.7, 0.23, 3.6, 1203.9),
    PublicComp("RPE20.NS", "Reliance Partners Enterprises", "Financials", "IND", 11610.4, 18.4, 0.43, 4.8, 631.0),
    PublicComp("TVSI38.NS", "TVS Infra India", "Industrials", "IND", 30034.9, 15.0, 0.39, 4.4, 2002.3),
    PublicComp("ACI41", "Apex Cloud Inc", "Tech", "US", 17485.4, 23.0, 0.37, 5.0, 760.2),
    PublicComp("GMRD74.NS", "GMR Diagnostics Ltd", "Healthcare", "IND", 7900.8, 8.7, 0.27, 4.5, 908.1),
    PublicComp("JCI33.NS", "Jindal Cyber India", "Tech", "IND", 5221.4, 9.0, 0.29, 5.3, 580.2),
    PublicComp("LTBI59.NS", "L&T Bank Industries", "Energy", "IND", 2755.2, 6.7, 0.34, 3.1, 411.2),
    PublicComp("RSI77.NS", "Reliance Steel Industries", "Industrials", "IND", 35579.5, 11.8, 0.41, 2.1, 3015.2),
    PublicComp("APC12", "Apex Partners Corp", "Financials", "US", 12858.7, 21.1, 0.59, 3.1, 609.4),
    PublicComp("ABLL77", "Atlas Bank LLC", "Energy", "US", 3355.2, 6.5, 0.27, 1.7, 516.2),
    PublicComp("BSE98.NS", "Bajaj Services Enterprises", "Equity Services", "IND", 30937.8, 17.8, 0.25, 3.3, 1738.1),
    PublicComp("SIG18", "Stellar Index Group", "Equity Services", "US", 38745.9, 16.2, 0.27, 2.8, 2391.7),
    PublicComp("MHE80.NS", "Mahindra Holdings Enterprises", "Energy", "IND", 35657.1, 22.7, 0.49, 5.9, 1570.8),
    PublicComp("JSWL15.NS", "JSW Lifestyle Enterprises", "Consumer", "IND", 37045.2, 8.4, 0.58, 5.2, 4410.1),
    PublicComp("GMRB95.NS", "GMR Brands Industries", "Consumer", "IND", 20032.5, 10.0, 0.49, 4.6, 2003.2),
    PublicComp("AAG39", "Atlas Asset Group", "Financials", "US", 22894.9, 14.6, 0.56, 4.7, 1568.1),
    PublicComp("NSC96", "Nexus Sys Corp", "Tech", "US", 19910.0, 7.8, 0.41, 1.6, 2552.6),
    PublicComp("GDI12.NS", "Godrej Digital India", "Tech", "IND", 49644.7, 21.6, 0.23, 2.4, 2298.4),
    PublicComp("SAG75", "Stellar Aero Group", "Industrials", "US", 24075.2, 22.6, 0.37, 5.3, 1065.3),
    PublicComp("CRI84", "Carlyle Ratings Inc", "Equity Services", "US", 3156.5, 15.0, 0.3, 2.6, 210.4),
    PublicComp("TCI89.NS", "Tata Cyber Industries", "Tech", "IND", 5505.2, 16.7, 0.33, 2.9, 329.7),
    PublicComp("ACG23", "Atlas Capital Group", "Energy", "US", 48798.2, 17.1, 0.33, 1.9, 2853.7),
    PublicComp("CTG81", "Crest Tech Group", "Tech", "US", 32294.4, 6.6, 0.44, 3.8, 4893.1),
    PublicComp("VHI79.NS", "Vedanta Health India", "Healthcare", "IND", 13831.9, 23.5, 0.33, 2.6, 588.6),
    PublicComp("JSWB65.NS", "JSW Bank India", "Financials", "IND", 21939.9, 10.9, 0.47, 4.8, 2012.8),
    PublicComp("CII91", "Crest Industrial Inc", "Industrials", "US", 10807.6, 24.0, 0.55, 3.2, 450.3),
    PublicComp("AMC24", "Apollo Markets Corp", "Equity Services", "US", 48759.0, 11.4, 0.5, 3.2, 4277.1),
    PublicComp("CCI61", "Crest Cyber Inc", "Tech", "US", 34287.1, 15.3, 0.5, 1.5, 2241.0),
    PublicComp("AHI79.NS", "Adani Health Industries", "Healthcare", "IND", 41310.7, 19.8, 0.52, 2.1, 2086.4),
    PublicComp("THE89.NS", "Tata Holdings Enterprises", "Energy", "IND", 8139.4, 8.1, 0.21, 5.6, 1004.9),
    PublicComp("LTRI49.NS", "L&T Ratings India", "Equity Services", "IND", 46131.2, 9.2, 0.46, 3.3, 5014.3),
    PublicComp("GRI84.NS", "Godrej Retail India", "Consumer", "IND", 18005.4, 9.3, 0.43, 3.6, 1936.1),
]

def find_comparable_companies(company: PrivateCompany, n_comps: int = 5) -> List[PublicComp]:
    """
    Find comparable companies for a private company.
    
    The selection process applies the following ranking:
    1. Filter by matching GICS sector.
    2. Rank by geography match (same geography preferred).
    3. Rank by size proximity (EBITDA within 0.25x to 4x of target).
    
    Args:
        company (PrivateCompany): The private target company.
        n_comps (int, optional): The number of comparable companies to return. Defaults to 5.
        
    Returns:
        list[PublicComp]: Top n_comps matching comparable companies.
    """
    logger.info(f"Finding comps for private company: {company.name} (Sector: {company.sector})")
    
    # 1. Filter by matching GICS sector
    sector_matches = [comp for comp in COMP_UNIVERSE if comp.sector.lower() == company.sector.lower()]
    
    # 2. Filter by size proximity (EBITDA within 0.25x to 4x of target)
    size_matches = []
    for comp in sector_matches:
        if company.ebitda > 0:
            ratio = comp.ebitda / company.ebitda
        else:
            ratio = 1.0 if comp.ebitda == 0 else 5.0
            
        if 0.25 <= ratio <= 4.0:
            size_matches.append(comp)
            
    # Fallback to sector matches if the size filter is too restrictive
    candidates = size_matches if len(size_matches) >= n_comps else sector_matches
    
    # Ranking function
    def score_comp(comp: PublicComp) -> float:
        score = 0.0
        
        # Rank by geography match
        if comp.geography.lower() == company.geography.lower():
            score += 10.0
            
        # Rank by size proximity (closer to 1.0 ratio is better)
        ratio = comp.ebitda / company.ebitda if company.ebitda > 0 else 5.0
        size_diff = abs(np.log(max(ratio, 0.01)))
        size_score = max(0.0, 5.0 - size_diff * 2)
        score += size_score
        
        return score
        
    candidates.sort(key=score_comp, reverse=True)
    return candidates[:n_comps]


def compute_peer_multiples(comps: List[PublicComp]) -> Dict[str, float]:
    """
    Compute median and mean multiple and metric statistics across the comp set.
    
    Args:
        comps (list[PublicComp]): A list of public comparable companies.
        
    Returns:
        dict: A dictionary containing computed median and mean metrics.
    """
    if not comps:
        logger.warning("Empty comp set provided. Returning empty dictionary.")
        return {}
        
    ev_ebitda = [c.ev_ebitda_multiple for c in comps]
    equity_vol = [c.equity_vol for c in comps]
    leverage = [c.leverage_ratio for c in comps]
    
    return {
        'median_ev_ebitda': float(np.median(ev_ebitda)),
        'mean_ev_ebitda': float(np.mean(ev_ebitda)),
        'median_equity_vol': float(np.median(equity_vol)),
        'mean_equity_vol': float(np.mean(equity_vol)),
        'median_leverage': float(np.median(leverage)),
        'mean_leverage': float(np.mean(leverage)),
        'n_comps': len(comps)
    }


def get_comp_set_for_portfolio(companies: List[PrivateCompany]) -> Dict[str, Dict[str, Any]]:
    """
    Retrieve comparable sets and peer multiples for a list of private companies.
    
    Args:
        companies (list[PrivateCompany]): List of private portfolio companies.
        
    Returns:
        dict[str, dict]: A mapping from company name to a dictionary containing its comps and multiples.
    """
    result = {}
    for company in companies:
        comps = find_comparable_companies(company)
        multiples = compute_peer_multiples(comps)
        
        result[company.name] = {
            'comps': comps,
            'multiples': multiples
        }
        
        logger.info(f"Processed comp set for {company.name}. Found {len(comps)} comps.")
        
    return result
