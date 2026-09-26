import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import math
import urllib.parse

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="PhageScope | Clinical Phage Directory",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "System"

if "selected_query" not in st.session_state:
    st.session_state["selected_query"] = None

if "lytic_only" not in st.session_state:
    st.session_state["lytic_only"] = True

# ---------------------------------------------------------
# Dynamic Theme CSS (System, Light, Dark)
# ---------------------------------------------------------
theme_mode = st.session_state["theme_mode"]

if theme_mode == "Dark":
    theme_css = """
    :root {
        --bg-main: #0b0f19;
        --bg-card: #131b2e;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
        --border-color: #243049;
        --stat-bg: #1c273e;
        --search-border: #38bdf8;
        --search-glow: rgba(56, 189, 248, 0.25);
        --tab-active: #38bdf8;
        --btn-bg: #1c273e;
        --btn-hover: #243049;
        --placeholder-color: #cbd5e1;
        --accent-green: #22c55e;
        --accent-green-bg: rgba(34, 197, 94, 0.15);
        --card-highlight: #18233c;
        --hero-bg: linear-gradient(180deg, rgba(56, 189, 248, 0.08) 0%, rgba(11, 15, 25, 0) 100%);
        --pill-bg: #1c273e;
        --pill-border: #243049;
        --pill-hover: #2a3b5c;
    }
    .stApp {
        background-color: var(--bg-main) !important;
        color: var(--text-main) !important;
    }
    header[data-testid="stHeader"] {
        background-color: var(--bg-main) !important;
    }
    """
    plotly_template = "plotly_dark"
elif theme_mode == "Light":
    theme_css = """
    :root {
        --bg-main: #f8fafc;
        --bg-card: #ffffff;
        --text-main: #0f172a;
        --text-muted: #64748b;
        --border-color: #e2e8f0;
        --stat-bg: #f1f5f9;
        --search-border: #0284c7;
        --search-glow: rgba(2, 132, 199, 0.18);
        --tab-active: #0284c7;
        --btn-bg: #ffffff;
        --btn-hover: #f1f5f9;
        --placeholder-color: #64748b;
        --accent-green: #15803d;
        --accent-green-bg: #dcfce7;
        --card-highlight: #f0f9ff;
        --hero-bg: linear-gradient(180deg, rgba(2, 132, 199, 0.06) 0%, rgba(248, 250, 252, 0) 100%);
        --pill-bg: #ffffff;
        --pill-border: #cbd5e1;
        --pill-hover: #f1f5f9;
    }
    .stApp {
        background-color: var(--bg-main) !important;
        color: var(--text-main) !important;
    }
    """
    plotly_template = "plotly_white"
else:  # System Default
    theme_css = """
    :root {
        --bg-main: #f8fafc;
        --bg-card: #ffffff;
        --text-main: #0f172a;
        --text-muted: #64748b;
        --border-color: #e2e8f0;
        --stat-bg: #f1f5f9;
        --search-border: #0284c7;
        --search-glow: rgba(2, 132, 199, 0.18);
        --tab-active: #0284c7;
        --btn-bg: #ffffff;
        --btn-hover: #f1f5f9;
        --placeholder-color: #64748b;
        --accent-green: #15803d;
        --accent-green-bg: #dcfce7;
        --card-highlight: #f0f9ff;
        --hero-bg: linear-gradient(180deg, rgba(2, 132, 199, 0.06) 0%, rgba(248, 250, 252, 0) 100%);
        --pill-bg: #ffffff;
        --pill-border: #cbd5e1;
        --pill-hover: #f1f5f9;
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-main: #0b0f19;
            --bg-card: #131b2e;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #243049;
            --stat-bg: #1c273e;
            --search-border: #38bdf8;
            --search-glow: rgba(56, 189, 248, 0.25);
            --tab-active: #38bdf8;
            --btn-bg: #1c273e;
            --btn-hover: #243049;
            --placeholder-color: #cbd5e1;
            --accent-green: #22c55e;
            --accent-green-bg: rgba(34, 197, 94, 0.15);
            --card-highlight: #18233c;
            --hero-bg: linear-gradient(180deg, rgba(56, 189, 248, 0.08) 0%, rgba(11, 15, 25, 0) 100%);
            --pill-bg: #1c273e;
            --pill-border: #243049;
            --pill-hover: #2a3b5c;
        }
        .stApp {
            background-color: var(--bg-main) !important;
            color: var(--text-main) !important;
        }
        header[data-testid="stHeader"] {
            background-color: var(--bg-main) !important;
        }
    }
    """
    plotly_template = "plotly_dark" if theme_mode == "Dark" else "plotly_white"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    {theme_css}
    
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, sans-serif;
    }}
    
    /* Remove default Streamlit top whitespace */
    .block-container,
    div[data-testid="stMainBlockContainer"] {{
        padding-top: 1.2rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1050px !important;
    }}
    header[data-testid="stHeader"] {{
        background: transparent !important;
        height: 2.2rem !important;
    }}
    
    /* Top Header Bar */
    .top-header-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 0 12px 0;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 24px;
    }}
    .brand-title {{
        font-size: 1.35rem;
        font-weight: 800;
        color: var(--text-main);
        display: flex;
        align-items: center;
        gap: 10px;
        letter-spacing: -0.02em;
    }}
    .brand-badge {{
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 3px 8px;
        border-radius: 6px;
        background: rgba(2, 132, 199, 0.12);
        color: #0284c7;
        border: 1px solid rgba(2, 132, 199, 0.25);
    }}

    /* Sleek Floating Theme Button in Top-Right */
    div.st-key-theme_cycle_btn {{
        position: absolute !important;
        top: 0.55rem !important;
        right: 0.8rem !important;
        z-index: 9999 !important;
        width: auto !important;
    }}
    div.st-key-theme_cycle_btn button {{
        border-radius: 50% !important;
        width: 36px !important;
        height: 36px !important;
        min-height: 36px !important;
        max-width: 36px !important;
        padding: 0 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: var(--stat-bg) !important;
        border: 1.5px solid var(--border-color) !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
        cursor: pointer !important;
        transition: transform 0.15s ease, border-color 0.15s ease !important;
    }}
    div.st-key-theme_cycle_btn button:hover {{
        border-color: #0284c7 !important;
        transform: scale(1.08) !important;
    }}
    /* Hide any abrupt 'Press Enter to apply' popup */
    div[data-testid="InputInstructions"] {{
        display: none !important;
    }}

    /* Google-Style Unified Search Box */
    div[data-testid="stSelectbox"]:has(div[data-baseweb="select"]),
    div[data-testid="stTextInput"] > div > div {{
        background: var(--bg-card) !important;
        border: 2px solid var(--search-border) !important;
        border-radius: 16px !important;
        padding: 4px 10px !important;
        box-shadow: 0 8px 30px -6px var(--search-glow), 0 2px 6px rgba(0, 0, 0, 0.04) !important;
        margin-top: 4px !important;
        margin-bottom: 12px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}
    div[data-testid="stSelectbox"]:has(div[data-baseweb="select"]):focus-within,
    div[data-testid="stTextInput"] > div > div:focus-within {{
        border-color: #0284c7 !important;
        box-shadow: 0 12px 36px -4px var(--search-glow) !important;
    }}
    div[data-baseweb="select"] > div {{
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    div[data-baseweb="select"] input,
    div[data-testid="stTextInput"] input {{
        font-size: 1.1rem !important;
        color: var(--text-main) !important;
        -webkit-text-fill-color: var(--text-main) !important;
    }}
    div[data-baseweb="select"] input::placeholder,
    div[data-testid="stTextInput"] input::placeholder {{
        color: var(--placeholder-color) !important;
        -webkit-text-fill-color: var(--placeholder-color) !important;
        opacity: 0.85 !important;
    }}
    /* Dropdown suggestions popover styling */
    div[data-baseweb="popover"],
    ul[data-baseweb="menu"],
    li[data-baseweb="menu-item"] {{
        background-color: var(--bg-card) !important;
        color: var(--text-main) !important;
        font-size: 0.95rem !important;
        border-radius: 12px !important;
    }}
    li[data-baseweb="menu-item"]:hover {{
        background-color: var(--card-highlight) !important;
        color: #0284c7 !important;
    }}
    .clinician-card {{
        background: var(--bg-card);
        border: 1.5px solid var(--border-color);
        border-radius: 14px;
        padding: 20px 22px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }}
    .clinician-card:hover {{
        border-color: #0284c7;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
    }}
    .card-top-row {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 14px;
        margin-bottom: 12px;
    }}
    .card-phage-title {{
        font-size: 1.35rem;
        font-weight: 800;
        color: var(--text-main);
    }}
    .target-pathogen-title {{
        font-size: 1.02rem;
        color: var(--text-muted);
        margin-top: 2px;
    }}
    .target-pathogen-title b {{
        color: var(--text-main);
        font-weight: 700;
    }}

    /* Badges */
    .badge {{
        display: inline-block;
        padding: 5px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }}
    .badge-lytic {{ 
        background-color: var(--accent-green-bg); 
        color: var(--accent-green); 
        border: 1px solid var(--accent-green); 
    }}
    .badge-other {{ 
        background-color: rgba(148, 163, 184, 0.18); 
        color: #64748b; 
        border: 1px solid rgba(148, 163, 184, 0.3); 
    }}

    /* SOURCING & CONTACT HIGHLIGHT BOX (The core clinician need!) */
    .sourcing-contact-box {{
        background: var(--card-highlight);
        border: 1.5px solid rgba(2, 132, 199, 0.28);
        border-radius: 12px;
        padding: 14px 16px;
        margin: 14px 0 16px 0;
    }}
    .sourcing-header {{
        font-size: 0.85rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #0284c7;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .sourcing-row {{
        display: flex;
        flex-direction: column;
        margin-bottom: 8px;
        gap: 2px;
    }}
    .sourcing-label {{
        font-weight: 600;
        font-size: 0.8rem;
        color: var(--text-muted);
    }}
    .sourcing-val {{
        font-weight: 600;
        font-size: 0.92rem;
        color: var(--text-main);
        word-break: break-word;
    }}

    /* Clinical Metrics Grid */
    .clinical-metrics-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        background: var(--stat-bg);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 14px;
    }}
    .c-metric-item {{
        display: flex;
        flex-direction: column;
    }}
    .c-metric-label {{
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        color: var(--text-muted);
        letter-spacing: 0.04em;
    }}
    .c-metric-val {{
        font-size: 0.92rem;
        font-weight: 700;
        color: var(--text-main);
        margin-top: 1px;
    }}

    /* Action Buttons inside Card */
    .contact-cta-button {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #0284c7;
        color: #ffffff !important;
        font-weight: 700;
        font-size: 0.88rem;
        padding: 9px 16px;
        border-radius: 9px;
        text-decoration: none !important;
        box-shadow: 0 2px 4px rgba(2, 132, 199, 0.2);
        transition: background-color 0.15s ease, transform 0.1s ease;
    }}
    .contact-cta-button:hover {{
        background-color: #0369a1;
        transform: translateY(-1px);
    }}
    .secondary-link-btn {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: var(--btn-bg);
        color: var(--text-main) !important;
        border: 1px solid var(--border-color);
        font-weight: 600;
        font-size: 0.88rem;
        padding: 9px 16px;
        border-radius: 9px;
        text-decoration: none !important;
        transition: border-color 0.15s ease;
    }}
    .secondary-link-btn:hover {{
        border-color: #0284c7;
    }}

    /* Global Text & Heading Fixes */
    h1, h2, h3, h4, h5, h6,
    [data-testid="stHeadingWithActionElements"] * {{
        color: var(--text-main) !important;
    }}
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] span,
    div[data-testid="stMarkdownContainer"] li {{
        color: var(--text-main);
    }}
    .stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{
        color: var(--text-muted) !important;
    }}

    /* Buttons Fix */
    .stDownloadButton button,
    .stButton button,
    button[data-testid="stBaseButton-secondary"],
    button[data-testid="stBaseButton-primary"] {{
        background-color: var(--btn-bg) !important;
        color: var(--text-main) !important;
        border: 1.5px solid var(--border-color) !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        transition: all 0.15s ease !important;
    }}
    .stDownloadButton button:hover,
    .stButton button:hover,
    button[data-testid="stBaseButton-secondary"]:hover {{
        background-color: var(--btn-hover) !important;
        border-color: var(--tab-active) !important;
        color: var(--tab-active) !important;
    }}

    /* Expanders */
    div[data-testid="stExpander"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
    }}
    div[data-testid="stExpander"] summary {{
        color: var(--text-main) !important;
    }}
    div[data-testid="stExpander"] summary span {{
        color: var(--text-main) !important;
        font-weight: 600 !important;
    }}

    /* Mobile media query */
    @media (max-width: 768px) {{
        .workflow-grid {{
            grid-template-columns: 1fr !important;
            gap: 12px !important;
        }}
        .hero-title {{
            font-size: 1.6rem !important;
        }}
        .hero-subtitle {{
            font-size: 0.95rem !important;
        }}
        .clinical-metrics-grid {{
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 8px !important;
        }}
        .card-top-row {{
            flex-direction: column !important;
            align-items: flex-start !important;
        }}
        .sourcing-row {{
            flex-direction: column !important;
            align-items: flex-start !important;
        }}
        .sourcing-val {{
            text-align: left !important;
        }}
    }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Data Helpers
# ---------------------------------------------------------
def clean_col_name(col: str) -> str:
    return col.replace(chr(176), "°").replace("\ufffd", "°").strip()

def parse_genome_size(val):
    if pd.isna(val):
        return None
    s = str(val).lower().strip()
    if "not reported" in s or "none" in s or "-" == s:
        return None
    m = re.search(r'([0-9]+(?:\.[0-9]+)?|\d{1,3}(?:,\d{3})+)', s)
    if not m:
        return None
    num_str = m.group(1).replace(',', '')
    try:
        num = float(num_str)
        if 'kb' in s:
            num *= 1000
        return num
    except ValueError:
        return None

def parse_gc(val):
    if pd.isna(val):
        return None
    s = str(val).lower().strip()
    if "not reported" in s or "-" == s:
        return None
    m = re.search(r'([0-9]+(?:\.[0-9]+)?)', s)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None

def normalize_phage_type(val):
    if pd.isna(val):
        return "Not reported"
    s = str(val).strip()
    s_lower = s.lower()
    if "lytic" in s_lower and "lysogenic" not in s_lower:
        return "Lytic"
    elif "lysogenic" in s_lower or "temperate" in s_lower:
        return "Lysogenic / Temperate"
    elif "engineered" in s_lower:
        return "Engineered"
    elif "not reported" in s_lower or s == "-" or s == "":
        return "Not reported"
    return s.capitalize()

def format_doi_url(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s or s.lower() in ["not reported", "-", "none"]:
        return None
    if s.startswith("http://") or s.startswith("https://"):
        return s
    return f"https://doi.org/{s}"

def extract_accession_link(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s or s.lower() in ["not reported", "-", "none"]:
        return None
    match_acc = re.search(r'\b([A-Z]{1,2}[0-9]{5,8}(?:\.[0-9]+)?)\b', s)
    if match_acc:
        acc = match_acc.group(1)
        return f"https://www.ncbi.nlm.nih.gov/nuccore/{acc}"
    match_prj = re.search(r'\b(PRJNA[0-9]+)\b', s)
    if match_prj:
        return f"https://www.ncbi.nlm.nih.gov/bioproject/{match_prj.group(1)}"
    return None

@st.cache_data
def load_data(csv_path: str = "LitSift_Extracted_Dataset.csv"):
    df = pd.read_csv(csv_path, encoding="utf-8", encoding_errors="replace")
    df.columns = [clean_col_name(c) for c in df.columns]

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(["nan", "None", "-"], "Not reported")

    df["Phage_Type_Clean"] = df["Phage type: Lytic/ Lysogenic/ Engineered"].apply(normalize_phage_type)
    df["Genome_Size_bp_num"] = df["Phage Genome size (bp)"].apply(parse_genome_size)
    df["GC_Content_num"] = df["Phage GC content (%)"].apply(parse_gc)
    df["DOI_URL"] = df["Article DOI"].apply(format_doi_url)
    df["NCBI_URL"] = df["Phage Genome Accession/Bioproject"].apply(extract_accession_link)
    
    # Pre-compute search corpus across all columns for fast multi-keyword search
    df["_search_corpus"] = df.apply(lambda row: " ".join(str(val) for val in row.values if pd.notna(val)), axis=1).str.lower()
    return df

def search_dataframe(data_df: pd.DataFrame, query: str) -> pd.DataFrame:
    if not query or not query.strip() or query == "__ALL__":
        return data_df.copy()
    words = [w.strip().lower() for w in re.split(r'\s+', query.strip()) if w.strip()]
    if not words:
        return data_df.copy()
    mask = pd.Series(True, index=data_df.index)
    for word in words:
        mask = mask & data_df["_search_corpus"].str.contains(word, case=False, na=False, regex=False)
    return data_df[mask]

# Load dataset
try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()


# ---------------------------------------------------------
# FLOATING COMPACT THEME TOGGLE (TOP-RIGHT CORNER)
# ---------------------------------------------------------
mode_icons = {"System": "💻", "Light": "☀️", "Dark": "🌙"}
mode_next = {"System": "Light", "Light": "Dark", "Dark": "System"}
current_icon = mode_icons.get(theme_mode, "💻")

if st.button(current_icon, key="theme_cycle_btn", help=f"Theme: {theme_mode} · Click to cycle"):
    st.session_state["theme_mode"] = mode_next.get(theme_mode, "System")
    st.rerun()


# ---------------------------------------------------------
# AUTO-SUGGESTIONS DICTIONARY (Pathogens, Phages, Locations, Samples, Accessions)
# ---------------------------------------------------------
hosts = sorted([h.strip() for h in df['Host Bacterial Species'].dropna().unique() if h.strip() and not h.startswith('Not')])
phages = sorted([p.strip() for p in df['Phage Name'].dropna().unique() if p.strip() and not p.startswith('Not')])
places = sorted([pl.strip() for pl in df['Place of Sample collection'].dropna().unique() if pl.strip() and not pl.startswith('Not')])
samples = sorted([s.strip() for s in df['Phage isolation Sample'].dropna().unique() if s.strip() and not s.startswith('Not')])
accessions = sorted([a.strip() for a in df['Phage Genome Accession/Bioproject'].dropna().unique() if a.strip() and not a.startswith('Not')])
common_keywords = ["Sewage", "India", "Manipal", "Mumbai", "Pune", "River water", "Hospital effluent", "Lytic", "MDR", "Capsid"]

search_suggestions = []
for item in hosts + phages + common_keywords + places + samples + accessions:
    if item and item not in search_suggestions:
        search_suggestions.append(item)


# ---------------------------------------------------------
# HEADER / BRANDING & AUTOCOMPLETE KEYWORD SEARCH
# ---------------------------------------------------------
active_query = st.session_state.get("selected_query")
is_searching = bool(active_query)

if is_searching:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; padding: 4px 0 10px 0;">
        <svg width="26" height="26" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" style="color: #0284c7; flex-shrink: 0;">
            <polygon points="18,2 25.5,6.5 25.5,14.5 18,18.5 10.5,14.5 10.5,6.5" fill="rgba(2, 132, 199, 0.2)" stroke-width="2" />
            <polyline points="10.5,6.5 18,10.5 25.5,6.5" stroke-width="1.2" opacity="0.65" />
            <polyline points="10.5,14.5 18,10.5 25.5,14.5" stroke-width="1.2" opacity="0.65" />
            <line x1="18" y1="2" x2="18" y2="10.5" stroke-width="1.2" opacity="0.65" />
            <line x1="18" y1="10.5" x2="18" y2="18.5" stroke-width="1.2" opacity="0.65" />
            <line x1="14.5" y1="19.5" x2="21.5" y2="19.5" stroke-width="2.4" />
            <line x1="16.5" y1="20" x2="16.5" y2="27" stroke-width="1.8" />
            <line x1="19.5" y1="20" x2="19.5" y2="27" stroke-width="1.8" />
            <polygon points="13.5,27 22.5,27 23.5,28.5 12.5,28.5" fill="currentColor" stroke-width="1" />
            <polyline points="13.5,28 7,26 3,34" stroke-width="1.9" />
            <polyline points="22.5,28 29,26 33,34" stroke-width="1.9" />
        </svg>
        <span style="font-size: 1.3rem; font-weight: 800; letter-spacing: -0.02em;">PhageScope</span>
        <span class="brand-badge">Clinical Directory</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align: center; padding: 36px 16px 14px 16px;">
        <svg width="46" height="46" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" style="color: #0284c7; margin-bottom: 8px;">
            <polygon points="18,2 25.5,6.5 25.5,14.5 18,18.5 10.5,14.5 10.5,6.5" fill="rgba(2, 132, 199, 0.2)" stroke-width="2" />
            <polyline points="10.5,6.5 18,10.5 25.5,6.5" stroke-width="1.2" opacity="0.65" />
            <polyline points="10.5,14.5 18,10.5 25.5,14.5" stroke-width="1.2" opacity="0.65" />
            <line x1="18" y1="2" x2="18" y2="10.5" stroke-width="1.2" opacity="0.65" />
            <line x1="18" y1="10.5" x2="18" y2="18.5" stroke-width="1.2" opacity="0.65" />
            <line x1="14.5" y1="19.5" x2="21.5" y2="19.5" stroke-width="2.4" />
            <line x1="16.5" y1="20" x2="16.5" y2="27" stroke-width="1.8" />
            <line x1="19.5" y1="20" x2="19.5" y2="27" stroke-width="1.8" />
            <polygon points="13.5,27 22.5,27 23.5,28.5 12.5,28.5" fill="currentColor" stroke-width="1" />
            <polyline points="13.5,28 7,26 3,34" stroke-width="1.9" />
            <polyline points="22.5,28 29,26 33,34" stroke-width="1.9" />
        </svg>
        <div style="font-size: 2.25rem; font-weight: 800; letter-spacing: -0.03em; color: var(--text-main); margin-bottom: 4px;">
            PhageScope
        </div>
    </div>
    """, unsafe_allow_html=True)

# Google-Style Suggestions Search Box (with Clear Button ONLY when dirty)
def reset_search():
    st.session_state["selected_query"] = None
    st.session_state["autocomplete_search"] = None

def on_search_change():
    st.session_state["selected_query"] = st.session_state.get("autocomplete_search")

def set_browse_all():
    st.session_state["selected_query"] = "__ALL__"
    st.session_state["autocomplete_search"] = None

current_selection = st.session_state.get("selected_query")
if current_selection == "__ALL__":
    current_selection = None

is_dirty = bool(current_selection)

# Make sure autocomplete_search in session_state is synced with current_selection
if st.session_state.get("autocomplete_search") != current_selection:
    st.session_state["autocomplete_search"] = current_selection

if is_dirty:
    s_col1, s_col2 = st.columns([5.2, 1.0], vertical_alignment="center")
    with s_col1:
        st.selectbox(
            "Search keywords",
            options=search_suggestions,
            index=search_suggestions.index(current_selection) if current_selection in search_suggestions else None,
            placeholder="🔍 Search by pathogen, phage, accession, location, or any keyword...",
            accept_new_options=True,
            filter_mode="fuzzy",
            label_visibility="collapsed",
            key="autocomplete_search",
            on_change=on_search_change
        )
    with s_col2:
        st.button("✕ Clear", key="clear_dirty_search_btn", on_click=reset_search, use_container_width=True)
else:
    st.selectbox(
        "Search keywords",
        options=search_suggestions,
        index=None,
        placeholder="🔍 Search by pathogen, phage, accession, location, or any keyword...",
        accept_new_options=True,
        filter_mode="fuzzy",
        label_visibility="collapsed",
        key="autocomplete_search",
        on_change=on_search_change
    )


# ---------------------------------------------------------
# VIEW LOGIC: LANDING PAGE vs CLINICAL RESULTS VIEW
# ---------------------------------------------------------
if not is_searching:
    # =====================================================
    # PURE MINIMAL LANDING PAGE
    # =====================================================
    st.markdown("<div style='text-align: center; margin-top: 14px;'>", unsafe_allow_html=True)
    st.button(f"🔍 Or browse all {len(df)} phages in catalog →", key="browse_all_landing", on_click=set_browse_all)
    st.markdown("</div>", unsafe_allow_html=True)

    # Re-positioned description moved BELOW the search box to reclaim top area
    st.markdown("""
    <div style="text-align: center; color: var(--text-muted); font-size: 0.95rem; max-width: 580px; margin: 34px auto 0 auto; line-height: 1.55;">
        Search peer-reviewed bacteriophages by bacterial pathogen, accession, or keyword to find <b>where and whom to contact</b> to acquire live phage samples or MTAs.
    </div>
    <div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; margin-top: 36px; padding-top: 16px; border-top: 1px solid var(--border-color); opacity: 0.85;">
        Curated across peer-reviewed studies on clinical MDR isolates · Direct DOI author links & NCBI GenBank accessions
    </div>
    """, unsafe_allow_html=True)

else:
    # =====================================================
    # CLINICAL RESULTS VIEW (DOCTOR-FIRST)
    # =====================================================
    is_browse_all = (active_query == "__ALL__")
    filtered_df = search_dataframe(df, active_query)

    # Results Header & Controls
    ctrl_col1, ctrl_col2 = st.columns([3.2, 1.2], vertical_alignment="center")

    with ctrl_col1:
        if is_browse_all:
            st.markdown(f"**Showing all {len(filtered_df)} phages in database**")
        else:
            st.markdown(f"Showing **{len(filtered_df)}** candidate phages for: **`{active_query}`**")

    with ctrl_col2:
        lytic_toggle = st.toggle("🛡️ Only Lytic (Therapeutic Safe)", value=st.session_state["lytic_only"], key="lytic_checkbox")
        st.session_state["lytic_only"] = lytic_toggle
        if lytic_toggle:
            filtered_df = filtered_df[filtered_df["Phage_Type_Clean"] == "Lytic"]

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    if filtered_df.empty:
        st.warning(f"No phages found matching `{active_query}` with the selected criteria.")
        st.info("💡 **Clinical Tip**: Try searching the genus name (e.g. *Pseudomonas*, *Klebsiella*) or turn off the **'Only Lytic'** filter.")
    else:
        # Pagination
        PAGE_SIZE = 8
        total_items = len(filtered_df)
        total_pages = max(1, math.ceil(total_items / PAGE_SIZE))

        if total_pages > 1:
            p_bar1, p_bar2 = st.columns([3, 1], vertical_alignment="center")
            with p_bar1:
                st.caption(f"Showing candidate records {1 if total_items > 0 else 0} - {min(PAGE_SIZE, total_items)} of {total_items}")
            with p_bar2:
                current_page = st.selectbox(
                    "Page",
                    options=list(range(1, total_pages + 1)),
                    format_func=lambda x: f"Page {x} of {total_pages}",
                    label_visibility="collapsed",
                    key="results_page_selector"
                )
            start_idx = (current_page - 1) * PAGE_SIZE
            end_idx = min(start_idx + PAGE_SIZE, total_items)
            page_records = filtered_df.iloc[start_idx:end_idx]
        else:
            page_records = filtered_df

        # Render Phage Cards
        for idx, row in page_records.iterrows():
            phage_name = row.get("Phage Name", "Unnamed Phage")
            host_name = row.get("Host Bacterial Species", "Unspecified Host")
            challenge_host = row.get("Experimental / Challenge Host", "")
            p_type = row.get("Phage_Type_Clean", "Not reported")
            badge_class = "badge-lytic" if p_type == "Lytic" else "badge-other"
            badge_text = "✓ Lytic (Therapeutic Safe)" if p_type == "Lytic" else f"⚠️ {p_type}"

            temp = row.get("Optimal Temperature (°C)", "Not reported")
            ph_val = row.get("Optimal pH", "Not reported")
            burst = row.get("Burst size (phage/infected bacterium)", "Not reported")
            latent = row.get("Latent period (min)", "Not reported")

            location = row.get("Place of Sample collection", "Not reported")
            sample_src = row.get("Phage isolation Sample", "Not reported")
            doi_url = row.get("DOI_URL")
            doi_raw = row.get("Article DOI", "")
            ncbi_url = row.get("NCBI_URL")
            accession_raw = row.get("Phage Genome Accession/Bioproject", "Not reported")

            # Sample email pre-fill
            email_subject = urllib.parse.quote(f"Phage Sample / MTA Request: {phage_name} (DOI: {doi_raw})")
            email_body = urllib.parse.quote(
                f"Dear Corresponding Author,\n\n"
                f"I am contacting you regarding your published study on bacteriophage '{phage_name}' (DOI: {doi_raw}).\n\n"
                f"We are evaluating phage therapy options for a clinical infection involving {host_name} "
                f"and would like to inquire whether a sample/aliquot of this phage is available for therapeutic evaluation or research "
                f"under a standard Material Transfer Agreement (MTA).\n\n"
                f"Looking forward to your response.\n\n"
                f"Sincerely,\n[Clinician / Researcher Name]\n[Hospital / Institution]"
            )
            mailto_link = f"mailto:?subject={email_subject}&body={email_body}"

            challenge_str = f" · <i>Challenge strain: {challenge_host}</i>" if challenge_host and challenge_host != 'Not reported' else ""
            doi_btn_html = f'<a href="{doi_url}" target="_blank" class="contact-cta-button">📄 Contact Author Lab via DOI ↗</a>' if doi_url else ''
            ncbi_btn_html = f'<a href="{ncbi_url}" target="_blank" class="secondary-link-btn">🧬 View NCBI Sequence ↗</a>' if ncbi_url else ''

            card_html = (
                f'<div class="clinician-card">'
                f'<div class="card-top-row">'
                f'<div>'
                f'<div class="card-phage-title">🦠 {phage_name}</div>'
                f'<div class="target-pathogen-title">Target Pathogen: <b>{host_name}</b>{challenge_str}</div>'
                f'</div>'
                f'<div><span class="badge {badge_class}">{badge_text}</span></div>'
                f'</div>'
                f'<div class="sourcing-contact-box">'
                f'<div class="sourcing-header">📦 Whom & Where to Contact for Samples</div>'
                f'<div class="sourcing-row"><span class="sourcing-label">📍 Isolation Lab / Location:</span><span class="sourcing-val">{location}</span></div>'
                f'<div class="sourcing-row"><span class="sourcing-label">💧 Sample Environment:</span><span class="sourcing-val">{sample_src}</span></div>'
                f'<div class="sourcing-row"><span class="sourcing-label">🧬 Accession / BioProject:</span><span class="sourcing-val">{accession_raw}</span></div>'
                f'<div style="margin-top: 12px; display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">'
                f'{doi_btn_html}'
                f'<a href="{mailto_link}" class="secondary-link-btn">✉️ Draft Sample Request Email</a>'
                f'{ncbi_btn_html}'
                f'</div>'
                f'</div>'
                f'<div class="clinical-metrics-grid">'
                f'<div class="c-metric-item"><span class="c-metric-label">Optimal Temp</span><span class="c-metric-val">{temp}</span></div>'
                f'<div class="c-metric-item"><span class="c-metric-label">Optimal pH</span><span class="c-metric-val">{ph_val}</span></div>'
                f'<div class="c-metric-item"><span class="c-metric-label">Burst Kinetics</span><span class="c-metric-val">{burst}</span></div>'
                f'<div class="c-metric-item"><span class="c-metric-label">Latent Period</span><span class="c-metric-val">{latent}</span></div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

            # Deep Details Collapsed
            plaque_char = row.get("Phage's Plaque characteristics/Shape", "Not reported")
            taxonomy = row.get("Phage Taxonomy", "Not reported")
            morphology = row.get("Phage TEM dimensions/Capsid morphology", "Not reported")
            similarity = row.get("Phage TEM shows structural similarity with", "Not reported")
            g_size = row.get("Phage Genome size (bp)", "Not reported")
            gc_val = row.get("Phage GC content (%)", "Not reported")
            moi_val = row.get("Optimal MOI", "Not reported")

            with st.expander(f"🔬 Virology & Genomic Details ({phage_name})", expanded=False):
                d1, d2 = st.columns(2)
                with d1:
                    st.markdown(f"**Taxonomy:** {taxonomy}")
                    st.markdown(f"**TEM Morphology:** {morphology}")
                    st.markdown(f"**Structural Similarity:** {similarity}")
                    st.markdown(f"**Plaque Characteristics:** {plaque_char}")
                with d2:
                    st.markdown(f"**Genome Size:** {g_size}")
                    st.markdown(f"**GC Content:** {gc_val}")
                    st.markdown(f"**Optimal MOI:** {moi_val}")
                    st.markdown(f"**Article DOI Reference:** `{doi_raw}`")

        # Bottom actions
        st.markdown("<br>", unsafe_allow_html=True)
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            csv_matches = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Matching Phages (CSV)",
                data=csv_matches,
                file_name=f"PhageScope_{active_query}_candidates.csv",
                mime="text/csv",
                use_container_width=True
            )
        with dl_col2:
            if st.button("← Back to Search", key="back_to_search_btn", use_container_width=True):
                st.session_state["selected_query"] = None
                st.rerun()

        # Optional Researcher Analytics (tucked away at the bottom)
        with st.expander("📊 View Cohort Analytics (for researchers)", expanded=False):
            st.caption("Distribution across matching phages:")
            top_hosts = filtered_df["Host Bacterial Species"].value_counts().head(8).reset_index()
            top_hosts.columns = ["Host Species", "Count"]

            fig_hosts = px.bar(
                top_hosts,
                x="Count",
                y="Host Species",
                orientation="h",
                title="Bacterial Host Frequency",
                color="Count",
                color_continuous_scale="Blues",
                template=plotly_template
            )
            fig_hosts.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=35, b=20), height=300)
            st.plotly_chart(fig_hosts, use_container_width=True)
