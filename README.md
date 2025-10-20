
# Patient Data (Yes/No Form + Dashboard)

This Streamlit app allows editing columns (L, M, N) as Yes/No, then reloads to show the updated row only (dashboard view).

## Files
- `streamlit_app.py` — Streamlit form and dashboard
- `apps_script_webapp.gs` — Apps Script Web App for updating Sheet
- `requirements.txt` — dependencies

## Setup
1. Deploy the Apps Script as a Web App (`apps_script_webapp.gs`):
   - Execute as: Me
   - Access: Anyone with the link
   - Copy the `/exec` URL.

2. Create `.streamlit/secrets.toml` with:
   ```toml
   SUBMIT_ENDPOINT = "https://script.google.com/macros/s/XXXX/exec"
   SUBMIT_SECRET = "CHANGE_THIS_SECRET"
   TARGET_GID = "0"
   ```

3. Run locally:
   ```bash
   pip install -r requirements.txt
   streamlit run streamlit_app.py
   ```

## Usage
- Edit row 5 → open `?row=5`
- Select Yes/No → Submit → auto reload → `?row=5&lock=1&view=dashboard`
