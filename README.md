
# ⚡ Fast Submit Template (Streamlit + GAS)

- GAS caches header (120s) and returns the **next screen data** in each POST response.
- Streamlit renders the next step **inline** after submit (no extra GET / no rerun).
- Result: much faster UX after each submit.

## Files
- `Code.gs` — Google Apps Script backend (Web App)
- `app_fast_submit.py` — Streamlit frontend
- `requirements.txt`

## Deploy GAS
1. Open https://script.google.com/ → New project
2. Paste `Code.gs`
3. Set `SHEET_ID` (already set to the ID you provided)
4. (Optional) set `TOKEN` and pass it from Streamlit secrets
5. Deploy → Web app → Execute as: **Me**; Who has access: **Anyone with the link** (or your domain)

## Streamlit secrets
```
[gas]
webapp_url = "https://script.google.com/macros/s/AKfycb.../exec"
# token = "MY_SHARED_SECRET"
```

## Run
```
streamlit run app_fast_submit.py
```

## URL
- Start: `?row=1&mode=edit1` → A–K + L–Q (Yes/No)
- Submit → inline A–C, R–U + V (Priority 1/2/3)
- Submit → inline final A–C, R–V (no form)
