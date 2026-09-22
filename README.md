# PubScope 🔭

**PubScope** is an open-source platform designed to transform dense scientific literature into structured, interactive, and searchable online databases.

The current dataset showcases phenotypic, genomic, morphological, and physiological characterizations extracted from **80 Open-Access (OA) peer-reviewed publications** (*PubScope Bacteriophage Dataset*).

## Key Features
- **🔍 Multi-Dimensional Filtering**: Search by organism, host species, lifecycle/phenotype, isolation origin, and genomic attributes.
- **🔗 Bi-Directional Academic Links**: Direct links to original publication DOIs and live NCBI Nucleotide / BioProject records.
- **🔬 Deep-Dive Profile Cards**: Detailed breakdown of every entry's ultrastructure, kinetics, and environmental stability.
- **📊 Interactive Visual Analytics**: Built-in Plotly distributions and multi-parameter scatter plots.
- **📥 One-Click Export**: Instant CSV download for filtered subsets or complete datasets.

---

## Local Development

Always use the project's virtual environment (`.venv`):

```powershell
# In PowerShell:
& .venv\Scripts\streamlit.exe run app.py
```

The application will be accessible at `http://localhost:8501`.

---

## Deploying Online (Free)

### 1. Streamlit Community Cloud (Recommended)
1. Fork or push this repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io) with GitHub.
3. Click **New app** -> Select your repo `PubScope` -> Main file: `app.py`.
4. Click **Deploy**.

### 2. Render.com
1. Create a new **Web Service** on [Render](https://render.com) linked to your GitHub repo.
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
