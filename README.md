
# Patient Treatment Dashboard (A–K before, A–C + L–R after Submit)

## Overview
- Before submit: show columns A–K and form “Patient treatment” (Yes/No for L/M/N)
- After submit: reload and show dashboard (A–C + L–R)

## Setup
1. Deploy the Apps Script (apps_script_webapp.gs) as Web App → copy /exec URL.
2. Create `.streamlit/secrets.toml`:
   ```toml
   SUBMIT_ENDPOINT = "https://script.google.com/macros/s/XXXX/exec"
   SUBMIT_SECRET = "CHANGE_THIS_SECRET"
   TARGET_GID = "0"
   ```
3. Run:
   ```bash
   pip install -r requirements.txt
   streamlit run streamlit_app.py
   ```
4. Open:
   - Edit mode: `?row=5`
   - Dashboard: auto reload → `?row=5&lock=1&view=dashboard`
