
# Patient Treatment — Card-grid v2

## What’s inside
- Patient Information uses the **same card-grid layout** (kv-grid / kv-card / kv-label / kv-value) both **before** and **after** submit.
- Pre-submit: shows **A–K** as cards + **Patient treatment** (Yes/No for L/M/N).
- Post-submit: shows **A–C + L–R** as cards (no tables).

## Setup
1) Deploy Apps Script (`apps_script_webapp.gs`) as Web App → copy `/exec` URL
2) Create `.streamlit/secrets.toml`
```
SUBMIT_ENDPOINT = "https://script.google.com/macros/s/XXXX/exec"
SUBMIT_SECRET   = "CHANGE_THIS_SECRET"
TARGET_GID      = "0"
```
3) Run
```
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Usage
- Edit mode: `?row=5`
- After submit → auto redirect to `?row=5&lock=1&view=dashboard`
