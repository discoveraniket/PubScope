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
    page_title="PhageScope",
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
    st.session_state["lytic_only"] = False

# ---------------------------------------------------------
# Client Device Detection (W3C Hints + User-Agent)
# ---------------------------------------------------------
def detect_client_is_mobile() -> bool:
    try:
        headers = st.context.headers
        if headers.get("sec-ch-ua-mobile") == "?1":
            return True
        ua = headers.get("user-agent", "").lower()
        mobile_keywords = [
            "mobile", "iphone", "android", "ipod", "webos",
            "blackberry", "iemobile", "opera mini"
        ]
        if any(keyword in ua for keyword in mobile_keywords):
            return True
    except Exception:
        pass
    return False

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
        --tab-inactive: #94a3b8;
        --btn-bg: #1c273e;
        --btn-hover: #243049;
        --placeholder-color: #cbd5e1;
        --accent-green: #22c55e;
        --accent-green-bg: rgba(34, 197, 94, 0.15);
        --card-highlight: #1e293b;
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
        --search-border: #0070F3;
        --search-glow: rgba(0, 112, 243, 0.18);
        --tab-active: #0070F3;
        --tab-inactive: #64748b;
        --btn-bg: #ffffff;
        --btn-hover: #f1f5f9;
        --placeholder-color: #64748b;
        --accent-green: #15803d;
        --accent-green-bg: #dcfce7;
        --card-highlight: #f8fafc;
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
        --search-border: #0070F3;
        --search-glow: rgba(0, 112, 243, 0.18);
        --tab-active: #0070F3;
        --tab-inactive: #64748b;
        --btn-bg: #ffffff;
        --btn-hover: #f1f5f9;
        --placeholder-color: #64748b;
        --accent-green: #15803d;
        --accent-green-bg: #dcfce7;
        --card-highlight: #f8fafc;
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
            --tab-inactive: #94a3b8;
            --btn-bg: #1c273e;
            --btn-hover: #243049;
            --placeholder-color: #cbd5e1;
            --accent-green: #22c55e;
            --accent-green-bg: rgba(34, 197, 94, 0.15);
            --card-highlight: #1e293b;
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
    
    /* Remove Massive Default Streamlit Top Whitespace */
    .block-container,
    div[data-testid="stMainBlockContainer"] {{
        padding-top: 1.8rem !important;
        padding-bottom: 2rem !important;
    }}
    header[data-testid="stHeader"] {{
        background: transparent !important;
        height: 2.5rem !important;
    }}
    
    /* Top Header Bar */
    .top-header-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 0 8px 0;
        margin-bottom: 8px;
    }}
    .brand-title {{
        font-size: 1.45rem;
        font-weight: 800;
        color: var(--text-main);
        display: flex;
        align-items: center;
        gap: 8px;
        letter-spacing: -0.02em;
    }}
    .brand-sub {{
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--text-muted);
    }}

    /* GOOGLE-STYLE UNIFIED SEARCH BOX */
    div[data-testid="stSelectbox"]:has(div[data-baseweb="select"]) {{
        background: var(--bg-card);
        border: 2px solid var(--search-border);
        border-radius: 16px;
        padding: 4px 6px;
        box-shadow: 0 8px 26px -4px var(--search-glow), 0 2px 4px rgba(0, 0, 0, 0.04);
        margin-top: 4px;
        margin-bottom: 12px;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    div[data-testid="stSelectbox"]:has(div[data-baseweb="select"]):focus-within {{
        border-color: #0284c7;
        box-shadow: 0 10px 32px -4px var(--search-glow);
    }}
    div[data-baseweb="select"] > div {{
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}
    div[data-baseweb="select"] input {{
        font-size: 1.05rem !important;
        color: var(--text-main) !important;
        -webkit-text-fill-color: var(--text-main) !important;
    }}
    div[data-baseweb="select"] input::placeholder,
    div[data-baseweb="select"] input::-webkit-input-placeholder {{
        color: var(--placeholder-color) !important;
        -webkit-text-fill-color: var(--placeholder-color) !important;
        opacity: 0.85 !important;
    }}

    /* Minimalist Theme Radio Switcher */
    div[data-testid="stRadio"] {{
        display: flex;
        justify-content: flex-end;
    }}
    div[data-testid="stRadio"] > div {{
        display: flex !important;
        flex-direction: row !important;
        gap: 0px !important;
        background: var(--stat-bg);
        border: 1px solid var(--border-color);
        border-radius: 9999px;
        padding: 2px 4px;
    }}
    div[data-testid="stRadio"] label {{
        padding: 2px 8px !important;
        margin: 0 !important;
        cursor: pointer !important;
        font-size: 0.85rem !important;
    }}
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {{
        font-size: 0.88rem !important;
        color: var(--text-main) !important;
    }}

    /* Clinician Action Card */
    .clinician-card {{
        background: var(--bg-card);
        border: 1.5px solid var(--border-color);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }}
    .clinician-card:hover {{
        border-color: #0284c7;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }}
    .card-top-row {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 8px;
    }}
    .card-phage-title {{
        font-size: 1.25rem;
        font-weight: 800;
        color: var(--text-main);
    }}
    .target-pathogen-title {{
        font-size: 0.95rem;
        color: var(--text-muted);
        margin-bottom: 12px;
    }}
    .target-pathogen-title b {{
        color: var(--text-main);
        font-weight: 700;
    }}

    /* Badges */
    .badge {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
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

    /* Clinical Viability Grid */
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

    /* Sourcing & Provenance Section */
    .sourcing-box {{
        background: var(--card-highlight);
        border: 1px dashed var(--border-color);
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 12px;
        font-size: 0.85rem;
    }}
    .sourcing-row {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 4px;
    }}
    .sourcing-label {{
        font-weight: 600;
        color: var(--text-muted);
    }}
    .sourcing-val {{
        font-weight: 600;
        color: var(--text-main);
        text-align: right;
    }}

    /* Action Buttons inside Card */
    .contact-cta-button {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #0284c7;
        color: #ffffff !important;
        font-weight: 700;
        font-size: 0.85rem;
        padding: 8px 14px;
        border-radius: 8px;
        text-decoration: none !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        transition: background-color 0.15s ease;
    }}
    .contact-cta-button:hover {{
        background-color: #0369a1;
    }}
    .secondary-link-btn {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: var(--btn-bg);
        color: var(--text-main) !important;
        border: 1px solid var(--border-color);
        font-weight: 600;
        font-size: 0.85rem;
        padding: 8px 14px;
        border-radius: 8px;
        text-decoration: none !important;
        transition: border-color 0.15s ease;
    }}
    .secondary-link-btn:hover {{
        border-color: #0284c7;
    }}

    /* GLOBAL TEXT VISIBILITY FIXES */
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

    /* BUTTONS FIX */
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

    /* EXPANDERS FIX */
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
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
        border-top: 1px solid var(--border-color) !important;
    }}

    /* Mobile media query */
    @media (max-width: 768px) {{
        .clinical-metrics-grid {{
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 8px !important;
        }}
        .brand-title {{
            font-size: 1.25rem !important;
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
    
    # Check for direct email column if enriched in the future
    email_col = next((c for c in df.columns if "email" in c.lower() or "author email" in c.lower()), None)
    if email_col:
        df["Contact_Email"] = df[email_col].replace(["nan", "None", "-", "Not reported"], None)
    else:
        df["Contact_Email"] = None

    return df

# Load the dataset
try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()


# ---------------------------------------------------------
# TOP MINIMAL HEADER BAR
# ---------------------------------------------------------
h_col1, h_col2 = st.columns([4, 1.2], vertical_alignment="center")

with h_col1:
    st.markdown("""
    <div style="display: flex; align-items: baseline; gap: 8px;">
        <span class="brand-title">
            <svg width="30" height="30" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" style="color: #0284c7; flex-shrink: 0; vertical-align: middle;">
                <!-- Icosahedral Capsid Head -->
                <polygon points="18,2 25.5,6.5 25.5,14.5 18,18.5 10.5,14.5 10.5,6.5" fill="rgba(2, 132, 199, 0.2)" stroke-width="2" />
                <polyline points="10.5,6.5 18,10.5 25.5,6.5" stroke-width="1.2" opacity="0.65" />
                <polyline points="10.5,14.5 18,10.5 25.5,14.5" stroke-width="1.2" opacity="0.65" />
                <line x1="18" y1="2" x2="18" y2="10.5" stroke-width="1.2" opacity="0.65" />
                <line x1="18" y1="10.5" x2="18" y2="18.5" stroke-width="1.2" opacity="0.65" />
                <!-- Collar / Neck Ring -->
                <line x1="14.5" y1="19.5" x2="21.5" y2="19.5" stroke-width="2.4" />
                <!-- Contractile Tail Sheath -->
                <line x1="16.5" y1="20" x2="16.5" y2="27" stroke-width="1.8" />
                <line x1="19.5" y1="20" x2="19.5" y2="27" stroke-width="1.8" />
                <!-- Sheath Striations / Protein Discs -->
                <line x1="15.5" y1="21.5" x2="20.5" y2="21.5" stroke-width="1.3" />
                <line x1="15.5" y1="23.5" x2="20.5" y2="23.5" stroke-width="1.3" />
                <line x1="15.5" y1="25.5" x2="20.5" y2="25.5" stroke-width="1.3" />
                <!-- Baseplate & Injection Pin -->
                <polygon points="13.5,27 22.5,27 23.5,28.5 12.5,28.5" fill="currentColor" stroke-width="1" />
                <line x1="18" y1="28.5" x2="18" y2="30.5" stroke-width="1.8" />
                <!-- Jointed Tail Fibers (Classic Knee-Bend Morphology) -->
                <polyline points="13.5,28 7,26 3,34" stroke-width="1.9" />
                <polyline points="14.5,28.5 10,29 7,34.5" stroke-width="1.6" />
                <polyline points="22.5,28 29,26 33,34" stroke-width="1.9" />
                <polyline points="21.5,28.5 26,29 29,34.5" stroke-width="1.6" />
            </svg>
            PhageScope
        </span>
    </div>
    <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 1px;">
        Search bacteriophage candidates tested against bacterial pathogens.
    </div>
    """, unsafe_allow_html=True)

with h_col2:
    theme_icons = ["💻", "☀️", "🌙"]
    icon_to_mode = {"💻": "System", "☀️": "Light", "🌙": "Dark"}
    mode_to_icon = {"System": "💻", "Light": "☀️", "Dark": "🌙"}
    current_icon = mode_to_icon.get(theme_mode, "💻")
    
    chosen_icon = st.radio(
        "Theme",
        options=theme_icons,
        index=theme_icons.index(current_icon),
        horizontal=True,
        label_visibility="collapsed",
        key="theme_radio_selector"
    )
    if icon_to_mode[chosen_icon] != theme_mode:
        st.session_state["theme_mode"] = icon_to_mode[chosen_icon]
        st.rerun()

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# AUTO-SUGGESTION KEYWORD DICTIONARY
# ---------------------------------------------------------
# Compile high-value search suggestions (Hosts, Phages, Key Locations)
all_hosts = sorted([h for h in df["Host Bacterial Species"].unique() if h != "Not reported"])
all_phages = sorted([p for p in df["Phage Name"].unique() if p != "Not reported"])
key_locations = sorted([loc for loc in df["Place of Sample collection"].unique() if loc != "Not reported"])

search_suggestions = []
# 1. Hosts first (primary clinical intent)
for h in all_hosts:
    count = (df["Host Bacterial Species"] == h).sum()
    search_suggestions.append(f"{h}")

# 2. Phage names
for p in all_phages:
    if p not in search_suggestions:
        search_suggestions.append(p)

# ---------------------------------------------------------
# GOOGLE-STYLE UNIFIED AUTO-COMPLETE SEARCH BOX
# ---------------------------------------------------------
search_choice = st.selectbox(
    "Search Pathogen or Phage",
    options=search_suggestions,
    index=search_suggestions.index(st.session_state["selected_query"]) if st.session_state["selected_query"] in search_suggestions else None,
    placeholder="🔍 Type pathogen (e.g. Pseudomonas aeruginosa, Klebsiella, E. coli), phage name, or accession...",
    accept_new_options=True,
    filter_mode="fuzzy",
    label_visibility="collapsed",
    key="autocomplete_search"
)

# Update session state query
if search_choice != st.session_state["selected_query"]:
    st.session_state["selected_query"] = search_choice

active_query = st.session_state["selected_query"]

# Quick Common Pathogen Chips (ESKAPE Pathogens)
chip_cols = st.columns([1, 1.4, 1.4, 1.5, 1.3, 1.2, 1.2])
with chip_cols[0]:
    st.caption("**Popular:**")
with chip_cols[1]:
    if st.button("P. aeruginosa", key="chip_pa", use_container_width=True):
        st.session_state["selected_query"] = "Pseudomonas aeruginosa"
        st.rerun()
with chip_cols[2]:
    if st.button("K. pneumoniae", key="chip_kp", use_container_width=True):
        st.session_state["selected_query"] = "Klebsiella pneumoniae"
        st.rerun()
with chip_cols[3]:
    if st.button("A. baumannii", key="chip_ab", use_container_width=True):
        st.session_state["selected_query"] = "Acinetobacter"
        st.rerun()
with chip_cols[4]:
    if st.button("S. aureus", key="chip_sa", use_container_width=True):
        st.session_state["selected_query"] = "Staphylococcus aureus"
        st.rerun()
with chip_cols[5]:
    if st.button("E. coli", key="chip_ec", use_container_width=True):
        st.session_state["selected_query"] = "Escherichia coli"
        st.rerun()
with chip_cols[6]:
    if st.button("Show All", key="chip_all", use_container_width=True):
        st.session_state["selected_query"] = None
        st.rerun()


# ---------------------------------------------------------
# Filter Dataset
# ---------------------------------------------------------
filtered_df = df.copy()

if active_query:
    q = active_query.lower().strip()
    match_mask = filtered_df.apply(
        lambda row: row.astype(str).str.lower().str.contains(q, regex=False).any(),
        axis=1
    )
    filtered_df = filtered_df[match_mask]

# Clinical safety filter: Option to show only strictly lytic phages
filter_bar1, filter_bar2 = st.columns([3, 1], vertical_alignment="center")
with filter_bar1:
    if active_query:
        st.markdown(f"Showing **{len(filtered_df)}** candidate phages for: `\"{active_query}\"`")
    else:
        st.markdown(f"Showing all **{len(filtered_df)}** phages in database across 80 Open-Access publications")

with filter_bar2:
    lytic_toggle = st.toggle("🛡️ Only Lytic (Therapeutic)", value=st.session_state["lytic_only"], key="lytic_checkbox")
    st.session_state["lytic_only"] = lytic_toggle
    if lytic_toggle:
        filtered_df = filtered_df[filtered_df["Phage_Type_Clean"] == "Lytic"]


# ---------------------------------------------------------
# RESEARCHER DETAILS & VISUAL ANALYTICS (Single-Click Expanders)
# ---------------------------------------------------------
with st.expander("📊 View Cohort Analytics & Distributions (for researchers)", expanded=False):
    st.caption("Aggregate insights across the matching bacteriophages.")
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

    scatter_df = filtered_df.dropna(subset=["Genome_Size_bp_num", "GC_Content_num"])
    if not scatter_df.empty:
        fig_scatter = px.scatter(
            scatter_df,
            x="Genome_Size_bp_num",
            y="GC_Content_num",
            color="Host Bacterial Species",
            hover_name="Phage Name",
            labels={"Genome_Size_bp_num": "Genome (bp)", "GC_Content_num": "GC (%)"},
            title="Genome Size vs GC Content (%)",
            height=340,
            template=plotly_template
        )
        fig_scatter.update_layout(margin=dict(l=10, r=10, t=35, b=20))
        st.plotly_chart(fig_scatter, use_container_width=True)


with st.expander("🩺 Clinical Sourcing Guide: How to Request & Acquire Phage Aliquots", expanded=False):
    st.markdown("""
    ### How to Source Phage Samples for MDR Infections:
    1. **Contact Author Labs Directly**:
       - Click the **`📄 Contact Authors / Article DOI`** button on any phage card.
       - Look for the **Corresponding Author** contact email in the publisher article header.
    2. **Material Transfer Agreement (MTA)**:
       - Research universities and medical institutes typically share live phage aliquots under standard academic MTA agreements for clinical/compassionate use or research.
    3. **NCBI Genomic Sequence / Synthesis**:
       - If physical sample acquisition is delayed by geographical borders, use the **`🧬 NCBI GenBank Accession`** to analyze the genome or commission synthetic phage engineering.
    """)


# ---------------------------------------------------------
# CLINICIAN ACTION CARDS FEED
# ---------------------------------------------------------
st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

if filtered_df.empty:
    st.info(f"No phages found matching `{active_query}` with the selected criteria. Try typing a broader genus (e.g. *Pseudomonas*, *Klebsiella*) or disable the 'Only Lytic' filter.")
else:
    # Pagination
    PAGE_SIZE = 10
    total_items = len(filtered_df)
    total_pages = max(1, math.ceil(total_items / PAGE_SIZE))

    if total_pages > 1:
        pag_col1, pag_col2 = st.columns([3, 1], vertical_alignment="center")
        with pag_col1:
            st.caption(f"Showing page items for {total_items} candidates")
        with pag_col2:
            current_page = st.selectbox(
                "Page Selector",
                options=list(range(1, total_pages + 1)),
                format_func=lambda x: f"Page {x} of {total_pages}",
                label_visibility="collapsed",
                key="page_dropdown"
            )
        start_idx = (current_page - 1) * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, total_items)
        page_records = filtered_df.iloc[start_idx:end_idx]
    else:
        page_records = filtered_df

    for _, row in page_records.iterrows():
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
        contact_email = row.get("Contact_Email")

        # Prepare mailto URL if email is present
        if contact_email:
            subject = urllib.parse.quote(f"Inquiry regarding Phage Sample: {phage_name} (PubScope)")
            body = urllib.parse.quote(
                f"Dear Dr.,\n\nI am contacting you regarding your publication on {phage_name} (DOI: {doi_raw}). "
                f"We are evaluating therapeutic phage candidates for an infection involving {host_name} and would like to inquire about sample availability or MTA.\n\nSincerely,"
            )
            contact_href = f"mailto:{contact_email}?subject={subject}&body={body}"
            contact_label = f"✉️ Email Corresponding Author ({contact_email}) ↗"
        elif doi_url:
            contact_href = doi_url
            contact_label = "📄 Contact Authors via Article DOI ↗"
        else:
            contact_href = None
            contact_label = "No Contact Link Available"

        st.markdown(f"""
        <div class="clinician-card">
            <div class="card-top-row">
                <div>
                    <div class="card-phage-title">🦠 {phage_name}</div>
                    <div class="target-pathogen-title">
                        Target Pathogen: <b>{host_name}</b>
                        {f" · <i>Challenge strain: {challenge_host}</i>" if challenge_host and challenge_host != 'Not reported' else ''}
                    </div>
                </div>
                <div>
                    <span class="badge {badge_class}">{badge_text}</span>
                </div>
            </div>
            
            <div class="clinical-metrics-grid">
                <div class="c-metric-item">
                    <span class="c-metric-label">Optimal Temp</span>
                    <span class="c-metric-val">{temp}</span>
                </div>
                <div class="c-metric-item">
                    <span class="c-metric-label">Optimal pH</span>
                    <span class="c-metric-val">{ph_val}</span>
                </div>
                <div class="c-metric-item">
                    <span class="c-metric-label">Burst Kinetics</span>
                    <span class="c-metric-val">{burst}</span>
                </div>
                <div class="c-metric-item">
                    <span class="c-metric-label">Latent Period</span>
                    <span class="c-metric-val">{latent}</span>
                </div>
            </div>

            <div class="sourcing-box">
                <div class="sourcing-row">
                    <span class="sourcing-label">📍 Isolation Location / Facility:</span>
                    <span class="sourcing-val">{location}</span>
                </div>
                <div class="sourcing-row">
                    <span class="sourcing-label">💧 Isolation Environment:</span>
                    <span class="sourcing-val">{sample_src}</span>
                </div>
                <div class="sourcing-row">
                    <span class="sourcing-label">🧬 NCBI Accession / BioProject:</span>
                    <span class="sourcing-val">{accession_raw}</span>
                </div>
            </div>

            <div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-top: 10px;">
                {f'<a href="{contact_href}" target="_blank" class="contact-cta-button">{contact_label}</a>' if contact_href else ''}
                {f'<a href="{ncbi_url}" target="_blank" class="secondary-link-btn">🧬 View NCBI Sequence ↗</a>' if ncbi_url else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Single-Click Researcher Deep Details
        with st.expander(f"🔬 Detailed Morphology & Biophysics ({phage_name})", expanded=False):
            d1, d2 = st.columns(2)
            with d1:
                st.markdown(f"**Taxonomy:** {row.get('Phage Taxonomy', 'Not reported')}")
                st.markdown(f"**Capsid / TEM Dimensions:** {row.get('Phage TEM dimensions/Capsid morphology', 'Not reported')}")
                st.markdown(f"**Structural Similarity:** {row.get('Phage TEM shows structural similarity with', 'Not reported')}")
                plaque_str = row.get("Phage's Plaque characteristics/Shape", 'Not reported')
                st.markdown(f"**Plaque Characteristics:** {plaque_str}")
            with d2:
                st.markdown(f"**Genome Size:** {row.get('Phage Genome size (bp)', 'Not reported')}")
                st.markdown(f"**GC Content:** {row.get('Phage GC content (%)', 'Not reported')}")
                st.markdown(f"**Optimal MOI:** {row.get('Optimal MOI', 'Not reported')}")
                st.markdown(f"**Article DOI Reference:** `{doi_raw}`")

    # CSV Download Options
    st.markdown("<br>", unsafe_allow_html=True)
    c_dl1, c_dl2 = st.columns(2)
    with c_dl1:
        csv_filtered = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Matching Phages (CSV)",
            data=csv_filtered,
            file_name="PubScope_matching_phages.csv",
            mime="text/csv",
            use_container_width=True
        )
    with c_dl2:
        csv_all = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📦 Download Complete Dataset (CSV)",
            data=csv_all,
            file_name="LitSift_Complete_Dataset.csv",
            mime="text/csv",
            use_container_width=True
        )
