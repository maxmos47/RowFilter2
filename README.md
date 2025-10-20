
# Patient Treatment — Card-grid v3

## What’s new
- Form edits **L–Q** (6 fields) as **Yes/No**
- **Patient information** uses the same card-grid layout before/after submit
  - Before submit: shows **A–K**
  - After submit: shows **A–C + R–U** (no group labels shown)
- Mobile-friendly fonts and spacing

## Setup
1) Deploy `apps_script_webapp.gs` as a Web App → copy `/exec` URL
2) Create `.streamlit/secrets.toml`:
```
SUBMIT_ENDPOINT = "https://script.google.com/macros/s/XXXX/exec"
SUBMIT_SECRET   = "CHANGE_THIS_SECRET"
TARGET_GID      = "0"
```
3) Run:
```
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Usage
- Edit/preview: `?row=5`
- After submit → auto redirects to `?row=5&lock=1&view=dashboard`
