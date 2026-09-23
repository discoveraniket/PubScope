import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import math

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="PubScope | Literature Dataset Explorer",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="collapsed",  # Mobile-friendly: don't block the screen on phones
)

# ---------------------------------------------------------
# Polished Mobile-First & Desktop CSS
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Metrics Responsive Grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        text-align: left;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 2px;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #64748b;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-lytic { background-color: #dcfce7; color: #15803d; }
    .badge-lysogenic { background-color: #f3e8ff; color: #7e22ce; }
    .badge-other { background-color: #f1f5f9; color: #475569; }

    /* Mobile Phage Card Component */
    .mobile-phage-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .mobile-phage-card:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.06);
    }
    .phage-card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 8px;
    }
    .phage-name-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
    }
    .phage-sub-title {
        font-size: 0.88rem;
        color: #475569;
        margin-bottom: 10px;
    }
    .phage-stats-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        background: #f8fafc;
        border-radius: 8px;
        padding: 10px;
        font-size: 0.82rem;
        margin-bottom: 10px;
    }
    .stat-item-label {
        color: #64748b;
        font-weight: 500;
    }
    .stat-item-val {
        color: #0f172a;
        font-weight: 600;
    }

    /* Links inside cards */
    .action-links {
        display: flex;
        gap: 12px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 6px;
    }

    /* Media query adjustments for mobile screens */
    @media (max-width: 768px) {
        .metrics-grid {
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 8px !important;
        }
        .metric-card {
            padding: 10px 12px !important;
            border-radius: 10px !important;
        }
        .metric-value {
            font-size: 1.35rem !important;
        }
        .metric-label {
            font-size: 0.7rem !important;
        }
        .mobile-phage-card {
            padding: 12px !important;
        }
        .phage-name-title {
            font-size: 1.05rem !important;
        }
        /* Make tab buttons wrap nicely on small screens */
        div[data-baseweb="tab-list"] {
            gap: 4px !important;
        }
        button[data-baseweb="tab"] {
            padding: 8px 10px !important;
            font-size: 0.82rem !important;
        }
    }
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
    
    return df

# Load the dataset
try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading dataset: {e}")
    st.stop()


# ---------------------------------------------------------
# Main Page Header & KPI Cards (Responsive CSS Grid)
# ---------------------------------------------------------
st.title("🔭 PubScope")
st.markdown(
    "Explore phenotypic, genomic, and physiological traits of bacteriophages extracted from **80 Open-Access (OA) research publications**."
)

# ---------------------------------------------------------
# Mobile-First Search & Inline Filter Controls
# ---------------------------------------------------------
# Prominent Top Search Bar (Instant Mobile Access)
search_query = st.text_input(
    "🔍 Search Phages, Hosts, Accessions, DOIs, Locations:",
    placeholder="e.g. Escherichia, Sfin-2, Pseudomonas, sewage, MK972831...",
    key="global_search"
)

# Expandable filter drawer (so mobile users don't need to open the sidebar)
with st.expander("🎛️ Detailed Filters (Host, Lifestyle, Isolation Source, Genome Size)", expanded=False):
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        all_hosts = sorted([h for h in df["Host Bacterial Species"].unique() if h != "Not reported"])
        selected_hosts = st.multiselect(
            "🧫 Host Bacterial Species",
            options=all_hosts,
            default=[],
            help="Select one or more bacterial hosts"
        )
        all_types = sorted(df["Phage_Type_Clean"].unique().tolist())
        selected_types = st.multiselect(
            "⚡ Phage Lifestyle",
            options=all_types,
            default=[],
            help="Select lifecycle (Lytic, Lysogenic, Engineered)"
        )
    with f_col2:
        sample_sources = sorted([s for s in df["Phage isolation Sample"].unique() if s != "Not reported"])
        selected_sample_type = st.multiselect(
            "💧 Isolation Sample Source",
            options=sample_sources,
            default=[],
            help="Filter by environment (sewage, water, poultry, etc.)"
        )
        valid_sizes = df["Genome_Size_bp_num"].dropna()
        if not valid_sizes.empty:
            min_size = int(valid_sizes.min())
            max_size = int(valid_sizes.max())
            size_range = st.slider(
                "📏 Genome Size Range (bp)",
                min_value=min_size,
                max_value=max_size,
                value=(min_size, max_size),
                step=5000
            )
        else:
            size_range = None

    if st.button("🔄 Reset Filters", key="reset_filters"):
        st.session_state["global_search"] = ""
        st.rerun()

# Apply filter logic
filtered_df = df.copy()

if search_query:
    q = search_query.lower()
    match_mask = filtered_df.apply(lambda row: row.astype(str).str.lower().str.contains(q, regex=False).any(), axis=1)
    filtered_df = filtered_df[match_mask]

if selected_hosts:
    filtered_df = filtered_df[filtered_df["Host Bacterial Species"].isin(selected_hosts)]

if selected_types:
    filtered_df = filtered_df[filtered_df["Phage_Type_Clean"].isin(selected_types)]

if selected_sample_type:
    filtered_df = filtered_df[filtered_df["Phage isolation Sample"].isin(selected_sample_type)]

if size_range and size_range != (min_size, max_size):
    filtered_df = filtered_df[
        (filtered_df["Genome_Size_bp_num"] >= size_range[0]) & 
        (filtered_df["Genome_Size_bp_num"] <= size_range[1])
    ]

# KPI Summary Cards (Pure Responsive CSS Grid)
n_hosts = filtered_df["Host Bacterial Species"].nunique()
n_lytic = (filtered_df["Phage_Type_Clean"] == "Lytic").sum()
n_sequenced = filtered_df["Genome_Size_bp_num"].notna().sum()

st.markdown(f"""
<div class="metrics-grid">
    <div class="metric-card">
        <div class="metric-label">Phage Records</div>
        <div class="metric-value">{len(filtered_df)} <span style="font-size: 0.9rem; color: #94a3b8; font-weight: 500;">/ {len(df)}</span></div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Target Hosts</div>
        <div class="metric-value">{n_hosts}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Lytic Phages</div>
        <div class="metric-value">{n_lytic}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Sequenced Genomes</div>
        <div class="metric-value">{n_sequenced}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Tabs Navigation
# ---------------------------------------------------------
tab_table, tab_deepdive, tab_viz, tab_about = st.tabs([
    "📋 Phage Directory", 
    "🔍 Deep-Dive Card", 
    "📊 Analytics", 
    "ℹ️ About"
])

# ---------------------------------------------------------
# TAB 1: Phage Directory (Cards vs Table)
# ---------------------------------------------------------
with tab_table:
    # Mode selector: default to Cards for smooth mobile reading
    header_col1, header_col2 = st.columns([1, 1])
    with header_col1:
        st.subheader("Bacteriophage Directory")
    with header_col2:
        view_mode = st.radio(
            "View Mode:",
            ["📱 Mobile Cards", "🖥️ Full Table"],
            horizontal=True,
            help="Choose 'Mobile Cards' for phones and 'Full Table' for desktop spreadsheets"
        )

    if filtered_df.empty:
        st.warning("No phages found matching the active search or filters. Try clearing some filters.")
    elif view_mode == "📱 Mobile Cards":
        # Card Feed with Pagination
        PAGE_SIZE = 10
        total_items = len(filtered_df)
        total_pages = max(1, math.ceil(total_items / PAGE_SIZE))
        
        pag_col1, pag_col2 = st.columns([2, 1])
        with pag_col1:
            st.caption(f"Showing {total_items} phages (10 per page)")
        with pag_col2:
            current_page = st.selectbox(
                "Page",
                options=list(range(1, total_pages + 1)),
                format_func=lambda x: f"Page {x} of {total_pages}",
                label_visibility="collapsed"
            )

        start_idx = (current_page - 1) * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, total_items)
        page_records = filtered_df.iloc[start_idx:end_idx]

        for _, row in page_records.iterrows():
            badge_class = "badge-lytic" if row["Phage_Type_Clean"] == "Lytic" else ("badge-lysogenic" if "Lysogenic" in row["Phage_Type_Clean"] else "badge-other")
            
            # Format display fields
            phage_name = row.get("Phage Name", "Unknown Phage")
            host_name = row.get("Host Bacterial Species", "Unspecified Host")
            p_type = row.get("Phage_Type_Clean", "Not reported")
            genome_size = row.get("Phage Genome size (bp)", "Not reported")
            gc_content = row.get("Phage GC content (%)", "Not reported")
            accession = row.get("Phage Genome Accession/Bioproject", "Not reported")
            location = row.get("Place of Sample collection", "Not reported")
            sample_src = row.get("Phage isolation Sample", "Not reported")
            doi_link = row.get("DOI_URL")
            ncbi_link = row.get("NCBI_URL")

            st.markdown(f"""
            <div class="mobile-phage-card">
                <div class="phage-card-header">
                    <div>
                        <div class="phage-name-title">🦠 {phage_name}</div>
                        <div class="phage-sub-title">Host: <b>{host_name}</b></div>
                    </div>
                    <span class="badge {badge_class}">{p_type}</span>
                </div>
                <div class="phage-stats-grid">
                    <div><span class="stat-item-label">Genome Size:</span> <span class="stat-item-val">{genome_size}</span></div>
                    <div><span class="stat-item-label">GC Content:</span> <span class="stat-item-val">{gc_content}</span></div>
                    <div><span class="stat-item-label">Accession:</span> <span class="stat-item-val">{accession[:25]}</span></div>
                    <div><span class="stat-item-label">Source:</span> <span class="stat-item-val">{sample_src[:22]}</span></div>
                </div>
                <div class="action-links">
                    {f'<a href="{ncbi_link}" target="_blank" style="color: #0284c7; text-decoration: none;">🔗 NCBI Accession ↗</a>' if ncbi_link else '<span style="color: #94a3b8;">No NCBI Link</span>'}
                    {f'<a href="{doi_link}" target="_blank" style="color: #0284c7; text-decoration: none;">📄 Paper DOI ↗</a>' if doi_link else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Mobile Collapsible Ultrastructure & Kinetics
            with st.expander(f"🔬 More Traits for {phage_name}", expanded=False):
                d1, d2 = st.columns(2)
                with d1:
                    st.markdown(f"**Taxonomy:** {row.get('Phage Taxonomy', 'Not reported')}")
                    st.markdown(f"**Capsid / TEM:** {row.get('Phage TEM dimensions/Capsid morphology', 'Not reported')}")
                    plaque_val = row.get("Phage's Plaque characteristics/Shape", 'Not reported')
                    st.markdown(f"**Plaques:** {plaque_val}")
                with d2:
                    st.markdown(f"**Optimal Temp:** {row.get('Optimal Temperature (°C)', 'Not reported')}")
                    st.markdown(f"**Optimal pH:** {row.get('Optimal pH', 'Not reported')}")
                    st.markdown(f"**Burst Size:** {row.get('Burst size (phage/infected bacterium)', 'Not reported')}")
                    st.markdown(f"**Latent Period:** {row.get('Latent period (min)', 'Not reported')}")
                    st.markdown(f"**Optimal MOI:** {row.get('Optimal MOI', 'Not reported')}")

    else:
        # Full Desktop Table View
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
        available_display_cols = [c for c in display_cols if c in filtered_df.columns]

        st.dataframe(
            filtered_df[available_display_cols],
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            height=500
        )

    # Export Buttons
    st.markdown("<br>", unsafe_allow_html=True)
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        csv_filtered = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered CSV",
            data=csv_filtered,
            file_name="PubScope_filtered_phages.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_dl2:
        csv_all = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📦 Download Complete CSV",
            data=csv_all,
            file_name="LitSift_Complete_Dataset.csv",
            mime="text/csv",
            use_container_width=True
        )


# ---------------------------------------------------------
# TAB 2: Phage Deep Dive (Inspector Card)
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
        
        for _, p in phage_rows.iterrows():
            st.markdown(f"""
            <div class="mobile-phage-card" style="padding: 20px; border-left: 4px solid #0070F3;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div style="font-size: 1.35rem; font-weight: 700; color: #0f172a;">🦠 {p.get('Phage Name', 'N/A')}</div>
                    <span class="badge badge-lytic">{p.get('Phage_Type_Clean', 'Unknown')}</span>
                </div>
                <div style="color: #64748b; font-size: 0.95rem; margin-bottom: 12px;">
                    Target Host: <b style="color: #0f172a;">{p.get('Host Bacterial Species', 'N/A')}</b>
                    {f" | Challenge Host: <i>{p.get('Experimental / Challenge Host')}</i>" if p.get('Experimental / Challenge Host') != 'Not reported' else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Responsive Sections (stacking on mobile)
            c1, c2 = st.columns(2)
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

            st.markdown("---")
            c3, c4 = st.columns(2)
            with c3:
                st.markdown("##### ⚡ Kinetics & Stability")
                st.markdown(f"**Optimal MOI:** {p.get('Optimal MOI', 'Not reported')}")
                st.markdown(f"**Latent Period:** {p.get('Latent period (min)', 'Not reported')}")
                st.markdown(f"**Burst Size:** {p.get('Burst size (phage/infected bacterium)', 'Not reported')}")
                st.markdown(f"**Optimal Temperature:** {p.get('Optimal Temperature (°C)', 'Not reported')}")
                st.markdown(f"**Optimal pH:** {p.get('Optimal pH', 'Not reported')}")

            with c4:
                st.markdown("##### 📍 Origin & Publication")
                st.markdown(f"**Sample Type:** {p.get('Phage isolation Sample', 'Not reported')}")
                st.markdown(f"**Location:** {p.get('Place of Sample collection', 'Not reported')}")
                st.markdown(f"**Article DOI:** `{p.get('Article DOI', 'Not reported')}`")
                if p.get("DOI_URL"):
                    st.markdown(f"[🔗 Open Publication DOI]({p['DOI_URL']})")
            
            if len(phage_rows) > 1:
                st.markdown("---")
    else:
        st.info("No phages found matching the active filters.")


# ---------------------------------------------------------
# TAB 3: Visual Analytics (Full-Width on Small Screens)
# ---------------------------------------------------------
with tab_viz:
    st.subheader("Visual Analytics & Distributions")

    # Host Frequency Bar Chart
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
    fig_hosts.update_layout(
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=10, t=35, b=20),
        height=380,
    )
    st.plotly_chart(fig_hosts, use_container_width=True)

    # Lifestyle Donut Chart
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
    fig_type.update_layout(margin=dict(l=10, r=10, t=35, b=20), height=340)
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
            title="Genome Size vs GC Content (Hover/Tap to inspect)",
            height=440
        )
        fig_scatter.update_layout(margin=dict(l=10, r=10, t=35, b=20), legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No records in current filter have both sequenced Genome Size and GC Content reported.")


# ---------------------------------------------------------
# TAB 4: About
# ---------------------------------------------------------
with tab_about:
    st.subheader("About PubScope")
    st.markdown("""
    **PubScope** is an open-source platform designed to make scientific literature characterization datasets accessible, interactive, and searchable online.

    ### 🔬 Current Dataset: LitSift Bacteriophages
    - Curated from **80 Open-Access (OA) peer-reviewed publications**.
    - Covers phenotypic, morphological, and genomic traits including:
      - **Genomics**: Genome size (bp), GC percentage, NCBI Accession numbers, and BioProject IDs.
      - **Taxonomy & Ultrastructure**: Order, Family, TEM morphology, capsid dimensions, and tail characteristics.
      - **Infection Biology**: Host bacterial species, challenge strains, plaque morphology, MOI, latent period, and burst size.
      - **Stability**: Temperature and pH tolerance ranges.
      - **Provenance**: Isolation sample types and geographical origins.

    ---
    ### 💻 Source Code & Deployment
    - Repository: [github.com/discoveraniket/PubScope](https://github.com/discoveraniket/PubScope)
    - Hosted with Streamlit Community Cloud.
    """)
