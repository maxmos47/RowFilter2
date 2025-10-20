
# Edit Columns L/M/N via Form → Show Updated Row

A Streamlit + Google Apps Script setup to edit columns L, M, and N in your Google Sheet, then display the updated row as a dashboard.

## Files
- `streamlit_app.py` — Streamlit app (form + display)
- `apps_script_webapp.gs` — Apps Script Web App to update the sheet
- `requirements.txt` — dependencies (`streamlit`, `pandas`, `requests`)

## Setup
1. Deploy the Google Apps Script (`apps_script_webapp.gs`) as a Web App.
   - Execute as: **Me**
   - Who has access: **Anyone with the link**
   - Copy the Web App URL (ends with `/exec`).
2. Set `.streamlit/secrets.toml`:
   ```toml
   SUBMIT_ENDPOINT = "https://script.google.com/macros/s/XXXXXX/exec"
   SUBMIT_SECRET = "CHANGE_THIS_SECRET"
   TARGET_GID = "0"
   ```
3. Run the app:
   ```bash
   pip install -r requirements.txt
   streamlit run streamlit_app.py
   ```

## Usage
- Edit by row: `?row=5`
- Or by ID: `?id=ABC&id_col=HN`
- Adjust L/M/N → Submit → App updates sheet via Apps Script → Refreshes and displays the full updated row.
