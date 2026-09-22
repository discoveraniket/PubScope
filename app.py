import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import urllib.parse

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="PubScope | Literature Dataset Explorer",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished scientific styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 4px;
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-lytic { background-color: #dcfce7; color: #15803d; }
    .badge-lysogenic { background-color: #f3e8ff; color: #7e22ce; }
    .badge-other { background-color: #f1f5f9; color: #475569; }

    .phage-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    .phage-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 6px;
    }
    .prop-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px dashed #e2e8f0;
    }
    .prop-name {
        font-weight: 500;
        color: #64748b;
    }
    .prop-val {
        font-weight: 600;
        color: #1e293b;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Data Helpers
# ---------------------------------------------------------
def clean_col_name(col: str) -> str:
    # Standardize degree symbol and spaces
    c = col.replace(chr(176), "°").replace("\ufffd", "°").strip()
    return c

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
    # Match standard NCBI Nucleotide accession or BioProject
    # Example: MK972831, OP797796, OR233736.1, PRJNA1098433, PQ724394
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

    # Clean text columns
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(["nan", "None", "-"], "Not reported")

    # Add normalized & parsed helper columns
    df["Phage_Type_Clean"] = df["Phage type: Lytic/ Lysogenic/ Engineered"].apply(normalize_phage_type)
    df["Genome_Size_bp_num"] = df["Phage Genome size (bp)"].apply(parse_genome_size)
    df["GC_Content_num"] = df["Phage GC content (%)"].apply(parse_gc)
    df["DOI_URL"] = df["Article DOI"].apply(format_doi_url)
    df["NCBI_URL"] = df["Phage Genome Accession/Bioproject"].apply(extract_accession_link)
    
    return df

# Load the dataset
try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()

# ---------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------
st.sidebar.markdown("## 🧬 PubScope Filters")
st.sidebar.markdown("Filter bacteriophage records by taxonomy, host, or genomics.")

# 1. Global text search
search_query = st.sidebar.text_input("🔍 Search Anything", placeholder="e.g. E. coli, Sfin-2, Ganges, Ganga...")

# 2. Host Bacterial Species Filter
all_hosts = sorted([h for h in df["Host Bacterial Species"].unique() if h != "Not reported"])
selected_hosts = st.sidebar.multiselect(
    "🧫 Host Bacterial Species",
    options=all_hosts,
    default=[],
    help="Select one or more bacterial hosts (leave empty to show all)"
)

# 3. Phage Type / Lifestyle
all_types = sorted(df["Phage_Type_Clean"].unique().tolist())
selected_types = st.sidebar.multiselect(
    "⚡ Phage Lifestyle",
    options=all_types,
    default=[],
    help="Select lifecycle (Lytic, Lysogenic, Engineered)"
)

# 4. Sample Isolation Origin
sample_sources = sorted([s for s in df["Phage isolation Sample"].unique() if s != "Not reported"])
selected_sample_type = st.sidebar.multiselect(
    "💧 Isolation Sample Source",
    options=sample_sources,
    default=[],
    help="Filter by isolation environment (sewage, water, poultry, etc.)"
)

# 5. Genome Size Range Slider
valid_sizes = df["Genome_Size_bp_num"].dropna()
if not valid_sizes.empty:
    min_size = int(valid_sizes.min())
    max_size = int(valid_sizes.max())
    size_range = st.sidebar.slider(
        "📏 Genome Size (bp)",
        min_value=min_size,
        max_value=max_size,
        value=(min_size, max_size),
        step=5000,
        help="Filter by sequenced genome length in base pairs"
    )
else:
    size_range = None

# Filter logic
filtered_df = df.copy()

if search_query:
    q = search_query.lower()
    # match against all string columns
    match_mask = filtered_df.apply(lambda row: row.astype(str).str.lower().str.contains(q, regex=False).any(), axis=1)
    filtered_df = filtered_df[match_mask]

if selected_hosts:
    filtered_df = filtered_df[filtered_df["Host Bacterial Species"].isin(selected_hosts)]

if selected_types:
    filtered_df = filtered_df[filtered_df["Phage_Type_Clean"].isin(selected_types)]

if selected_sample_type:
    filtered_df = filtered_df[filtered_df["Phage isolation Sample"].isin(selected_sample_type)]

if size_range:
    # Keep records within range OR those without reported size if no slider restriction
    if size_range != (min_size, max_size):
        filtered_df = filtered_df[
            (filtered_df["Genome_Size_bp_num"] >= size_range[0]) & 
            (filtered_df["Genome_Size_bp_num"] <= size_range[1])
        ]

# Reset button
if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Powered by **PubScope** · Extracted from 80 Open-Access publications.")


# ---------------------------------------------------------
# Main Page Header & KPI Cards
# ---------------------------------------------------------
st.title("🔭 PubScope | Scientific Literature Data Explorer")
st.markdown(
    "Explore curated biological, morphological, and genomic traits extracted from **80 Open-Access (OA) scientific publications** *(PubScope Bacteriophage Dataset)*."
)

# Metric KPI summary cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Phage Records</div>
        <div class="metric-value">{len(filtered_df)} <span style="font-size: 1rem; color: #94a3b8;">/ {len(df)}</span></div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    n_hosts = filtered_df["Host Bacterial Species"].nunique()
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Target Bacterial Hosts</div>
        <div class="metric-value">{n_hosts}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    n_lytic = (filtered_df["Phage_Type_Clean"] == "Lytic").sum()
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Lytic Phages</div>
        <div class="metric-value">{n_lytic}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    n_sequenced = filtered_df["Genome_Size_bp_num"].notna().sum()
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Sequenced Genomes</div>
        <div class="metric-value">{n_sequenced}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ---------------------------------------------------------
# Tabs Navigation
# ---------------------------------------------------------
tab_table, tab_deepdive, tab_viz, tab_about = st.tabs([
    "📋 Dataset Explorer", 
    "🔍 Phage Inspector (Deep Dive)", 
    "📊 Visual Analytics", 
    "ℹ️ About & Deploy Guide"
])

# ---------------------------------------------------------
# TAB 1: Dataset Explorer Table
# ---------------------------------------------------------
with tab_table:
    st.subheader("Bacteriophage Data Table")
    st.caption(f"Displaying {len(filtered_df)} matching bacteriophage records. Click any column header to sort.")

    # Column configuration for clickable links & neat rendering
    column_config = {
        "DOI_URL": st.column_config.LinkColumn(
            "Article DOI Link",
            help="Direct link to original research paper",
            validate=r"^https://",
            display_text=r"https://doi.org/(.*)"
        ),
        "NCBI_URL": st.column_config.LinkColumn(
            "NCBI Accession Link",
            help="Direct link to GenBank or BioProject",
            validate=r"^https://",
            display_text="View on NCBI ↗"
        ),
        "Genome_Size_bp_num": st.column_config.NumberColumn(
            "Genome Size (bp)",
            format="%d bp"
        ),
        "GC_Content_num": st.column_config.NumberColumn(
            "GC Content (%)",
            format="%.2f %%"
        )
    }

    # Pick user-facing columns to display cleanly
    display_cols = [
        "Phage Name",
        "Host Bacterial Species",
        "Phage_Type_Clean",
        "Phage Genome Accession/Bioproject",
        "NCBI_URL",
        "Genome_Size_bp_num",
        "GC_Content_num",
        "Phage Taxonomy",
        "Place of Sample collection",
        "Phage isolation Sample",
        "DOI_URL",
        "Optimal Temperature (°C)",
        "Optimal pH",
        "Optimal MOI",
        "Latent period (min)",
        "Burst size (phage/infected bacterium)",
    ]
    
    # Filter only available columns
    available_display_cols = [c for c in display_cols if c in filtered_df.columns]

    st.dataframe(
        filtered_df[available_display_cols],
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=520
    )

    # Export Buttons
    col_dl1, col_dl2 = st.columns([1, 1])
    with col_dl1:
        csv_filtered = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv_filtered,
            file_name="PubScope_filtered_phages.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_dl2:
        csv_all = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📦 Download Complete Dataset (CSV)",
            data=csv_all,
            file_name="LitSift_Complete_Dataset.csv",
            mime="text/csv",
            use_container_width=True
        )


# ---------------------------------------------------------
# TAB 2: Phage Inspector (Deep Dive Card)
# ---------------------------------------------------------
with tab_deepdive:
    st.subheader("🔍 Phage Profile Inspector")
    st.caption("Select a specific bacteriophage to view its complete physiological, genomic, and morphological card.")

    if not filtered_df.empty:
        phage_names = filtered_df["Phage Name"].dropna().unique().tolist()
        selected_phage_name = st.selectbox(
            "Select Phage:",
            options=phage_names,
            index=0
        )
        
        phage_rows = filtered_df[filtered_df["Phage Name"] == selected_phage_name]
        
        for idx, p in phage_rows.iterrows():
            st.markdown(f"""
            <div class="phage-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div class="phage-title">🦠 {p.get('Phage Name', 'N/A')}</div>
                    <div>
                        <span class="badge badge-lytic">{p.get('Phage_Type_Clean', 'Unknown')}</span>
                    </div>
                </div>
                <div style="color: #64748b; font-size: 0.95rem; margin-bottom: 16px;">
                    Target Host: <b style="color: #0f172a;">{p.get('Host Bacterial Species', 'N/A')}</b> 
                    {f" | Challenge Host: <i>{p.get('Experimental / Challenge Host')}</i>" if p.get('Experimental / Challenge Host') != 'Not reported' else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown("##### 🧬 Genomic Profile")
                st.markdown(f"**Accession / BioProject:** {p.get('Phage Genome Accession/Bioproject', 'Not reported')}")
                if p.get("NCBI_URL"):
                    st.markdown(f"[🔗 View on NCBI Nuccore / BioProject]({p['NCBI_URL']})")
                st.markdown(f"**Genome Size:** {p.get('Phage Genome size (bp)', 'Not reported')}")
                st.markdown(f"**GC Content:** {p.get('Phage GC content (%)', 'Not reported')}")
                st.markdown(f"**Taxonomy:** {p.get('Phage Taxonomy', 'Not reported')}")

            with c2:
                st.markdown("##### 🔬 Morphology & Plaque")
                st.markdown(f"**TEM Dimensions / Capsid:** {p.get('Phage TEM dimensions/Capsid morphology', 'Not reported')}")
                st.markdown(f"**Structural Similarity:** {p.get('Phage TEM shows structural similarity with', 'Not reported')}")
                plaque_char = p.get("Phage's Plaque characteristics/Shape", 'Not reported')
                st.markdown(f"**Plaque Characteristics:** {plaque_char}")

            with c3:
                st.markdown("##### ⚡ Kinetics & Stability")
                st.markdown(f"**Optimal MOI:** {p.get('Optimal MOI', 'Not reported')}")
                st.markdown(f"**Latent Period:** {p.get('Latent period (min)', 'Not reported')}")
                st.markdown(f"**Burst Size:** {p.get('Burst size (phage/infected bacterium)', 'Not reported')}")
                st.markdown(f"**Optimal Temperature:** {p.get('Optimal Temperature (°C)', 'Not reported')}")
                st.markdown(f"**Optimal pH:** {p.get('Optimal pH', 'Not reported')}")

            st.markdown("---")
            c4, c5 = st.columns(2)
            with c4:
                st.markdown("##### 📍 Origin & Isolation")
                st.markdown(f"**Sample Type:** {p.get('Phage isolation Sample', 'Not reported')}")
                st.markdown(f"**Location:** {p.get('Place of Sample collection', 'Not reported')}")
            with c5:
                st.markdown("##### 📄 Publication Reference")
                st.markdown(f"**Article DOI:** `{p.get('Article DOI', 'Not reported')}`")
                if p.get("DOI_URL"):
                    st.markdown(f"[🔗 Open Publication (DOI: {p.get('Article DOI')})]({p['DOI_URL']})")
            
            if len(phage_rows) > 1:
                st.markdown("---")
    else:
        st.info("No phages found matching the active filters.")


# ---------------------------------------------------------
# TAB 3: Visual Analytics
# ---------------------------------------------------------
with tab_viz:
    st.subheader("Visual Analytics & Distributions")

    viz_col1, viz_col2 = st.columns(2)

    with viz_col1:
        # Host Distribution
        top_hosts = filtered_df["Host Bacterial Species"].value_counts().head(10).reset_index()
        top_hosts.columns = ["Host Species", "Count"]
        
        fig_hosts = px.bar(
            top_hosts,
            x="Count",
            y="Host Species",
            orientation="h",
            title="Top 10 Bacterial Hosts in Filtered Set",
            color="Count",
            color_continuous_scale="Blues",
        )
        fig_hosts.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=20, r=20, t=40, b=20), height=380)
        st.plotly_chart(fig_hosts, use_container_width=True)

    with viz_col2:
        # Phage Lifestyle Donut Chart
        type_counts = filtered_df["Phage_Type_Clean"].value_counts().reset_index()
        type_counts.columns = ["Lifestyle", "Count"]

        fig_type = px.pie(
            type_counts,
            names="Lifestyle",
            values="Count",
            title="Phage Lifestyle Distribution",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_type.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=380)
        st.plotly_chart(fig_type, use_container_width=True)

    # Genome Size vs GC Content Scatter Plot
    st.markdown("##### 🧬 Genome Size vs. GC Content (%)")
    scatter_df = filtered_df.dropna(subset=["Genome_Size_bp_num", "GC_Content_num"])

    if not scatter_df.empty:
        fig_scatter = px.scatter(
            scatter_df,
            x="Genome_Size_bp_num",
            y="GC_Content_num",
            color="Host Bacterial Species",
            hover_name="Phage Name",
            hover_data=["Phage Taxonomy", "Phage Genome Accession/Bioproject"],
            labels={
                "Genome_Size_bp_num": "Genome Size (bp)",
                "GC_Content_num": "GC Content (%)",
                "Host Bacterial Species": "Host"
            },
            title="Genome Size vs GC Content (Hover to inspect individual phages)",
            height=480
        )
        fig_scatter.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No records in current filter have both sequenced Genome Size and GC Content reported.")


# ---------------------------------------------------------
# TAB 4: About & Deploy Guide
# ---------------------------------------------------------
with tab_about:
    st.subheader("About the PubScope Dataset & Deployment Guide")
    st.markdown("""
    ### 🔬 About PubScope Dataset
    This dataset compiles granular phenotypic, morphological, and genomic data points extracted from **80 Open-Access (OA) research articles** on bacteriophage isolation and characterization.

    #### Cataloged Properties:
    - **Genomics**: Genome size (bp), GC percentage, NCBI Accession numbers, and BioProject references.
    - **Taxonomy & Ultrastructure**: Order, Family, TEM morphology, capsid dimensions, and tail characteristics.
    - **Infection Biology**: Host bacterial species, challenge strains, plaque morphology, MOI, latent period, and burst size.
    - **Stability**: Temperature and pH tolerance ranges.
    - **Provenance**: Isolation sample types and geographical origins.

    ---

    ### 🚀 How to Host This Streamlit App Online

    #### Option 1: Streamlit Community Cloud (Recommended & 100% Free)
    1. **Push your code to GitHub**:
       - Make sure your repository has:
         - `LitSift_Extracted_Dataset.csv`
         - `app.py`
         - `requirements.txt`
    2. **Deploy on Streamlit Cloud**:
       - Visit [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
       - Click **"New App"**.
       - Choose your repository (`username/reponame`), branch (`main`), and file path (`app.py`).
       - Click **Deploy**! In about 1-2 minutes, you will get a permanent public URL (e.g. `https://litsift-phages.streamlit.app`).

    #### Option 2: Render.com (Web Service)
    1. Create a new **Web Service** on [Render](https://render.com).
    2. Connect your GitHub repository.
    3. Configure:
       - **Environment**: `Python 3`
       - **Build Command**: `pip install -r requirements.txt`
       - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
    4. Click **Create Web Service**.
    """)
