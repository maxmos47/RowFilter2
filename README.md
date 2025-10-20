
# Patient Treatment Card-grid (Mobile UI)

## Features
- Responsive 3-column card grid for patient data (A–K before submit)
- "Patient treatment" Yes/No form for L/M/N
- After submit → Dashboard view with A–C + L–R (card layout, no tables)

## Setup
1. Deploy Apps Script (apps_script_webapp.gs) as Web App (anyone with link).
2. Create `.streamlit/secrets.toml`:
   ```toml
   SUBMIT_ENDPOINT = "https://script.google.com/macros/s/XXXX/exec"
   SUBMIT_SECRET = "CHANGE_THIS_SECRET"
   TARGET_GID = "0"
   ```
3. Run app:
   ```bash
   pip install -r requirements.txt
   streamlit run streamlit_app.py
   ```

Usage:
- Edit: `?row=5`
- After submit → `?row=5&lock=1&view=dashboard`
