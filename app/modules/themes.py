# app/modules/themes.py
import streamlit as st


THEMES = {
    "Ocean": {
        "brand": "#0ea5e9", 
        "bg": "#f0f9ff",
        "card": "#ffffff", 
        "text": "#0f172a", 
        "muted": "#64748b", 
        "border": "#cbd5e1",
        "accent": "#06b6d4", 
        "shadow": "rgba(14, 165, 233, 0.15)",
    },
    "Sunset": {
        "brand": "#f43f5e", 
        "bg": "#fff1f2",
        "card": "#ffffff", 
        "text": "#111827", 
        "muted": "#6b7280", 
        "border": "#fecdd3",
        "accent": "#f97316", 
        "shadow": "rgba(244, 63, 94, 0.15)",
    },
    "Emerald": {
        "brand": "#10b981", 
        "bg": "#f0fdf4",
        "card": "#ffffff", 
        "text": "#064e3b", 
        "muted": "#047857", 
        "border": "#bbf7d0",
        "accent": "#34d399", 
        "shadow": "rgba(16, 185, 129, 0.15)",
    },
    "Dark": {
        "brand": "#60a5fa", 
        "bg": "#0f172a",
        "card": "#1e293b", 
        "text": "#f1f5f9", 
        "muted": "#cbd5e1", 
        "border": "#334155",
        "accent": "#93c5fd", 
        "shadow": "rgba(96, 165, 250, 0.2)",
    },
}


def inject(theme_name: str = "Ocean"):
    c = THEMES.get(theme_name, THEMES["Ocean"])
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    
    /* === ROOT === */
    :root {{
        --brand: {brand};
        --bg: {bg};
        --card: {card};
        --text: {text};
        --muted: {muted};
        --border: {border};
        --accent: {accent};
        --shadow: {shadow};
    }}
    
    * {{
        font-family: 'Inter', -apple-system, sans-serif;
    }}
    
    /* Background */
    .stApp {{
        background: var(--bg);
    }}
    
    /* === SIDEBAR === */
    [data-testid="stSidebar"] {{
        background: var(--card);
        border-right: 2px solid var(--border);
        box-shadow: 4px 0 20px var(--shadow);
    }}
    
    [data-testid="stSidebar"] label {{
        color: var(--text) !important;
        font-weight: 700;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }}
    
    /* Sidebar selectbox text - FORCE VISIBLE */
    [data-testid="stSidebar"] .stSelectbox select {{
        color: var(--text) !important;
        background: var(--card) !important;
    }}
    
    [data-testid="stSidebar"] .stSelectbox div {{
        color: var(--text) !important;
    }}
    
    /* === METRICS === */
    [data-testid="stMetricValue"] {{
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--brand) !important;
        letter-spacing: -1px;
    }}
    
    [data-testid="stMetricLabel"] {{
        font-size: 0.75rem;
        font-weight: 700;
        color: var(--text) !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    div[data-testid="metric-container"] {{
        background: var(--card);
        padding: 1.75rem;
        border-radius: 16px;
        border: 2px solid var(--border);
        box-shadow: 0 4px 16px var(--shadow);
        transition: all 0.3s ease;
    }}
    
    div[data-testid="metric-container"]:hover {{
        transform: translateY(-4px);
        box-shadow: 0 8px 24px var(--shadow);
        border-color: var(--brand);
    }}
    
    /* === BUTTONS WITH WHITE TEXT === */
    .stButton > button {{
        background: linear-gradient(135deg, var(--brand), var(--accent)) !important;
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.75rem;
        font-weight: 700;
        font-size: 0.875rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px var(--shadow);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px var(--shadow);
    }}
    
    .stButton button * {{
        color: white !important;
    }}
    
    /* === FILE UPLOADER WITH WHITE BUTTON TEXT === */
    [data-testid="stFileUploader"] {{
        background: var(--card);
        border: 3px dashed var(--border);
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: 0 4px 16px var(--shadow);
        transition: all 0.3s ease;
    }}
    
    [data-testid="stFileUploader"]:hover {{
        border-color: var(--brand);
        border-style: solid;
    }}
    
    [data-testid="stFileUploader"] button {{
        background: linear-gradient(135deg, var(--brand), var(--accent)) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.625rem 1.25rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        box-shadow: 0 4px 12px var(--shadow) !important;
    }}
    
    [data-testid="stFileUploader"] button * {{
        color: white !important;
    }}
    
    [data-testid="stFileUploader"] label {{
        color: var(--text) !important;
        font-weight: 600 !important;
    }}
    
    /* === DATAFRAME === */
    [data-testid="stDataFrame"] {{
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid var(--border);
        box-shadow: 0 4px 16px var(--shadow);
    }}
    
    .dataframe thead th {{
        background: linear-gradient(135deg, var(--brand), var(--accent)) !important;
        color: white !important;
        font-weight: 700 !important;
        padding: 0.875rem !important;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.5px;
    }}
    
    .dataframe tbody td {{
        padding: 0.75rem !important;
        border-bottom: 1px solid var(--border) !important;
        color: var(--text) !important;
        font-weight: 500 !important;
    }}
    
    .dataframe tbody tr:hover {{
        background: rgba(14, 165, 233, 0.05) !important;
    }}
    
    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        background: var(--card);
        padding: 0.625rem;
        border-radius: 12px;
        border: 2px solid var(--border);
        box-shadow: 0 4px 16px var(--shadow);
    }}
    
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        padding: 0.625rem 1.5rem;
        font-weight: 700;
        font-size: 0.813rem;
        color: var(--text) !important;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, var(--brand), var(--accent)) !important;
        color: white !important;
        box-shadow: 0 4px 12px var(--shadow);
    }}
    
    .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {{
        background: rgba(14, 165, 233, 0.1);
    }}
    
    /* === INPUTS & LABELS === */
    .stTextInput label, .stNumberInput label, .stSelectbox label, .stMultiSelect label, .stRadio label {{
        color: var(--text) !important;
        font-weight: 700 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }}
    
    .stTextInput input, .stNumberInput input {{
        border-radius: 10px;
        border: 2px solid var(--border) !important;
        padding: 0.75rem;
        color: var(--text) !important;
        background: var(--card) !important;
        transition: all 0.3s ease;
        font-weight: 500;
    }}
    
    /* === SELECTBOX - NUCLEAR OPTION FOR TEXT VISIBILITY === */
    /* Force select element text */
    .stSelectbox select {{
        border-radius: 10px;
        border: 2px solid var(--border) !important;
        padding: 0.75rem !important;
        color: var(--text) !important;
        background: var(--card) !important;
        transition: all 0.3s ease;
        font-weight: 600 !important;
    }}
    
    /* Force all option text */
    .stSelectbox option {{
        color: var(--text) !important;
        background: var(--card) !important;
        font-weight: 600 !important;
    }}
    
    /* BaseWeb select container - all children */
    .stSelectbox [data-baseweb="select"] {{
        background: var(--card) !important;
        color: var(--text) !important;
    }}
    
    .stSelectbox [data-baseweb="select"] * {{
        color: var(--text) !important;
    }}
    
    /* Dropdown value display */
    .stSelectbox [data-baseweb="select"] > div {{
        color: var(--text) !important;
        background: var(--card) !important;
    }}
    
    /* Inner value container */
    .stSelectbox [data-baseweb="select"] > div > div {{
        color: var(--text) !important;
    }}
    
    /* Dropdown arrow icon - CRITICAL */
    .stSelectbox [data-baseweb="select"] svg {{
        fill: var(--text) !important;
        color: var(--text) !important;
        stroke: var(--text) !important;
    }}
    
    /* Dropdown menu when opened */
    .stSelectbox [role="listbox"] {{
        background: var(--card) !important;
        border: 2px solid var(--border) !important;
        box-shadow: 0 8px 24px var(--shadow) !important;
    }}
    
    /* Dropdown options */
    .stSelectbox [role="option"] {{
        color: var(--text) !important;
        background: var(--card) !important;
        padding: 0.75rem 1rem !important;
        font-weight: 600 !important;
    }}
    
    .stSelectbox [role="option"]:hover {{
        background: rgba(14, 165, 233, 0.15) !important;
        color: var(--text) !important;
    }}
    
    /* Selected option */
    .stSelectbox [role="option"][aria-selected="true"] {{
        background: rgba(14, 165, 233, 0.2) !important;
        color: var(--text) !important;
        font-weight: 700 !important;
    }}
    
    /* === RADIO BUTTONS === */
    .stRadio [role="radiogroup"] {{
        color: var(--text) !important;
    }}
    
    .stRadio [role="radio"] {{
        color: var(--text) !important;
    }}
    
    .stRadio label {{
        color: var(--text) !important;
        font-weight: 600 !important;
    }}
    
    /* === MULTISELECT === */
    .stMultiSelect [data-baseweb="select"] {{
        background: var(--card) !important;
    }}
    
    .stMultiSelect [data-baseweb="select"] input {{
        color: var(--text) !important;
    }}
    
    .stMultiSelect [data-baseweb="select"] * {{
        color: var(--text) !important;
    }}
    
    .stMultiSelect [data-baseweb="select"] svg {{
        fill: var(--text) !important;
        color: var(--text) !important;
    }}
    
    .stMultiSelect [data-baseweb="popover"] {{
        background: var(--card) !important;
    }}
    
    .stMultiSelect [data-baseweb="popover"] * {{
        color: var(--text) !important;
    }}
    
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {{
        border-color: var(--brand) !important;
        box-shadow: 0 0 0 3px var(--shadow);
    }}
    
    /* === SLIDERS === */
    .stSlider label {{
        color: var(--text) !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        font-size: 0.75rem !important;
    }}
    
    .stSlider [role="slider"] {{
        background: var(--brand) !important;
    }}
    
    /* === EXPANDER === */
    .streamlit-expanderHeader {{
        background: var(--card);
        border-radius: 12px;
        border: 2px solid var(--border);
        padding: 0.875rem 1.25rem;
        font-weight: 700;
        color: var(--text) !important;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px var(--shadow);
    }}
    
    .streamlit-expanderHeader:hover {{
        border-color: var(--brand);
        box-shadow: 0 4px 16px var(--shadow);
    }}
    
    /* === HEADERS === */
    h1, h2, h3 {{
        color: var(--text) !important;
        font-weight: 800;
        letter-spacing: -0.5px;
    }}
    
    h1 {{ font-size: 2.5rem; }}
    h2 {{ font-size: 2rem; margin-top: 2rem; }}
    h3 {{ font-size: 1.5rem; margin-top: 1.5rem; }}
    
    /* === SUCCESS/INFO/WARNING === */
    .stSuccess {{
        background: #d1fae5 !important;
        border-left: 4px solid #10b981 !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        color: #065f46 !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2) !important;
    }}
    
    .stSuccess * {{
        color: #065f46 !important;
    }}
    
    .stInfo {{
        background: #dbeafe !important;
        border-left: 4px solid #3b82f6 !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        color: #1e40af !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2) !important;
    }}
    
    .stInfo * {{
        color: #1e40af !important;
    }}
    
    .stWarning {{
        background: #fef3c7 !important;
        border-left: 4px solid #f59e0b !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        color: #92400e !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.2) !important;
    }}
    
    .stWarning * {{
        color: #92400e !important;
    }}
    
    /* === JSON/CODE BLOCKS === */
    .stJson, pre, code {{
        background: #1e293b !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        border: 2px solid var(--border) !important;
    }}
    
    .stJson *, pre *, code * {{
        color: inherit !important;
        font-family: 'Consolas', 'Monaco', monospace !important;
    }}
    
    [data-testid="stJson"] {{
        background: #1e293b !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        border: 2px solid var(--border) !important;
    }}
    
    [data-testid="stJson"] * {{
        color: inherit !important;
    }}
    
    /* === DIVIDER === */
    hr {{
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--brand), transparent);
        margin: 2rem 0;
    }}
    
    /* === PLOTLY CHARTS === */
    .js-plotly-plot {{
        border-radius: 12px;
        border: 2px solid var(--border);
        overflow: hidden;
        box-shadow: 0 4px 16px var(--shadow);
        min-height: 500px !important;
    }}
    
    .js-plotly-plot .plotly {{
        min-height: 500px !important;
    }}
    
    .js-plotly-plot .main-svg {{
        min-height: 500px !important;
    }}
    
    [data-testid="stPlotlyChart"] {{
        min-height: 500px !important;
    }}
    
    [data-testid="stPlotlyChart"] > div {{
        min-height: 500px !important;
    }}
    
    /* === SCROLLBAR === */
    ::-webkit-scrollbar {{
        width: 10px;
        height: 10px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: var(--bg);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: var(--brand);
        border-radius: 5px;
        border: 2px solid var(--bg);
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--accent);
    }}
    
    /* === GENERAL TEXT === */
    .stMarkdown p {{
        color: var(--text) !important;
    }}
    
    p {{
        color: var(--text) !important;
    }}
    
    /* === MULTISELECT TAGS === */
    .stMultiSelect [data-baseweb="tag"] {{
        background: var(--brand) !important;
        color: white !important;
        font-weight: 600;
        border-radius: 6px;
    }}
    
    /* === DOWNLOAD BUTTON === */
    [data-testid="stDownloadButton"] button {{
        background: linear-gradient(135deg, var(--brand), var(--accent)) !important;
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.75rem;
        font-weight: 700;
        text-transform: uppercase;
        box-shadow: 0 4px 12px var(--shadow);
    }}
    
    [data-testid="stDownloadButton"] button * {{
        color: white !important;
    }}
    
    /* === MOBILE RESPONSIVE === */
    @media (max-width: 768px) {{
        h1 {{ font-size: 2rem; }}
        h2 {{ font-size: 1.5rem; }}
        h3 {{ font-size: 1.25rem; }}
        
        [data-testid="stMetricValue"] {{
            font-size: 1.75rem;
        }}
        
        .stButton > button {{
            width: 100%;
        }}
        
        .js-plotly-plot {{
            min-height: 400px !important;
        }}
    }}
    </style>
    """.format(**c)
    st.markdown(css, unsafe_allow_html=True)
