
import streamlit as st
import pandas as pd
import requests
from typing import Dict, List

st.set_page_config(page_title="Row Dashboard", page_icon="🩺", layout="centered")

# =========================
# CONFIG: GAS Web App URL
# =========================
# Put your deployed Google Apps Script Web App URL in .streamlit/secrets.toml
# [gas]
# webapp_url = "https://script.google.com/macros/s/AKfycb.../exec"
# token = "MY_SHARED_SECRET"     # (optional, only if you set TOKEN in GAS)
GAS_WEBAPP_URL = st.secrets.get("gas", {}).get("webapp_url", "")
TOKEN = st.secrets.get("gas", {}).get("token", "")  # optional shared secret

ALLOWED_V = ["Priority 1", "Priority 2", "Priority 3"]
YN = ["Yes", "No"]

# =========================
# Helpers for query params
# =========================
def get_query_params():
    try:
        q = st.query_params
        return {k: v for k, v in q.items()}
    except Exception:
        return {k: v[0] for k, v in st.experimental_get_query_params().items()}

def set_query_params(**kwargs):
    try:
        st.query_params.clear()
        st.query_params.update(kwargs)
    except Exception:
        st.experimental_set_query_params(**kwargs)

# =========================
# GAS calls
# =========================
def gas_get_row(row: int) -> dict:
    params = {"action": "get", "row": str(row)}
    if TOKEN:
        params["token"] = TOKEN
    r = requests.get(GAS_WEBAPP_URL, params=params, timeout=25)
    r.raise_for_status()
    return r.json()

def gas_update_lq(row: int, lq_values: Dict[str, str]) -> dict:
    # Send JSON as a form field
    payload = {"action": "update_lq", "row": str(row), "lq": pd.Series(lq_values).to_json()}
    if TOKEN:
        payload["token"] = TOKEN
    r = requests.post(GAS_WEBAPP_URL, data=payload, timeout=25)
    r.raise_for_status()
    return r.json()

def gas_update_v(row: int, v_value: str) -> dict:
    payload = {"action": "update_v", "row": str(row), "value": v_value}
    if TOKEN:
        payload["token"] = TOKEN
    r = requests.post(GAS_WEBAPP_URL, data=payload, timeout=25)
    r.raise_for_status()
    return r.json()

# =========================
# Card UI (mobile-friendly)
# =========================
st.markdown("""
<style>
.kv-card{border:1px solid #e5e7eb;padding:12px;border-radius:14px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,0.06);background:#fff;}
.kv-label{font-size:0.9rem;color:#6b7280;margin-bottom:2px;}
.kv-value{font-size:1.05rem;font-weight:600;word-break:break-word;}
@media (max-width: 640px){
  .kv-card{padding:12px;}
  .kv-value{font-size:1.06rem;}
}
</style>
""", unsafe_allow_html=True)

def _pairs_from_row(df_one_row: pd.DataFrame) -> List[tuple[str, str]]:
    s = df_one_row.iloc[0]
    pairs = []
    for col in df_one_row.columns:
        val = s[col]
        if pd.isna(val):
            val = ""
        pairs.append((str(col), str(val)))
    return pairs

def render_kv_grid(df_one_row: pd.DataFrame, title: str = "", cols: int = 2):
    if title:
        st.subheader(title)
    items = _pairs_from_row(df_one_row)
    n = len(items)
    for i in range(0, n, cols):
        row_items = items[i:i+cols]
        col_objs = st.columns(len(row_items))
        for c, (label, value) in zip(col_objs, row_items):
            with c:
                st.markdown(
                    f"""
                    <div class="kv-card">
                      <div class="kv-label">{label}</div>
                      <div class="kv-value">{value if value!='' else '-'}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# =========================
# Main UI
# =========================
st.markdown("### 🩺 Patient Information")

if not GAS_WEBAPP_URL:
    st.error("Missing GAS web app URL. Add to secrets:\n\n[gas]\nwebapp_url = \"https://script.google.com/macros/s/XXX/exec\"")
    st.stop()

qp = get_query_params()
row_str = qp.get("row", "1")
mode = qp.get("mode", "edit1")  # "edit1" -> first phase (L-Q); "edit2" -> second phase (V); "view" -> final

try:
    row = int(row_str)
    if row < 1:
        row = 1
except ValueError:
    row = 1

# Fetch the row via GAS
try:
    data = gas_get_row(row=row)
except Exception as e:
    st.error(f"Failed to fetch row via GAS: {e}")
    st.stop()

if data.get("status") != "ok":
    st.error(f"GAS error: {data}")
    st.stop()

# Build DataFrames from GAS response
df_AK = pd.DataFrame([data.get("A_K", {})])
df_AC_RU = pd.DataFrame([data.get("A_C_R_U", {})])
df_AC_RV = pd.DataFrame([data.get("A_C_R_V", {})])
max_row = data.get("max_rows", 1)

# L-Q info
headers_LQ = data.get("headers_LQ", ["L","M","N","O","P","Q"])
current_LQ = data.get("current_LQ", [])  # list of Yes/No in same order
current_V = data.get("current_V", "")

# =========================
# Modes
# =========================
if mode == "view":
    # Final view: A-C, R-V (no form)
    render_kv_grid(df_AC_RV, title="Patient", cols=2)
    st.success("Final view (no form).")
    if st.button("Edit again (L–Q)"):
        set_query_params(row=str(row), mode="edit1")
        st.rerun()

elif mode == "edit2":
    # After first submit: show A–C, R–U and form for V
    render_kv_grid(df_AC_RU, title="Patient", cols=2)
    st.markdown("#### Secondary Triage")
    idx = ALLOWED_V.index(current_V) if current_V in ALLOWED_V else 0
    with st.form("form_v", border=True):
        v_value = st.selectbox("Select Triage priority", ALLOWED_V, index=idx)
        submitted = st.form_submit_button("Submit")
        if submitted:
            try:
                res = gas_update_v(row=row, v_value=v_value)
                if res.get("status") == "ok":
                    set_query_params(row=str(row), mode="view")
                    st.rerun()
                else:
                    st.error(f"Update V failed: {res}")
            except Exception as e:
                st.error(f"Failed to update V via GAS: {e}")

else:
    # edit1 (default): show A–K + form for L–Q (Yes/No checkboxes)
    render_kv_grid(df_AK, title="Patient", cols=2)

    st.markdown("#### Treatment")
    # We will show checkboxes in two columns
    l_col, r_col = st.columns(2)
    selections = {}

    # Ensure we have values for 6 columns
    curr_vals = current_LQ if current_LQ and len(current_LQ) == 6 else ["No"] * 6

    with st.form("form_lq", border=True):
        with l_col:
            for i, label in enumerate(headers_LQ[:3]):
                default = True if curr_vals[i] == "Yes" else False
                chk = st.checkbox(f"{label}", value=default)
                selections[label] = "Yes" if chk else "No"
        with r_col:
            for i, label in enumerate(headers_LQ[3:6], start=3):
                default = True if curr_vals[i] == "Yes" else False
                chk = st.checkbox(f"{label}", value=default)
                selections[label] = "Yes" if chk else "No"

        submitted = st.form_submit_button("Submit")
        if submitted:
            try:
                res = gas_update_lq(row=row, lq_values=selections)
                if res.get("status") == "ok":
                    set_query_params(row=str(row), mode="edit2")
                    st.rerun()
                else:
                    st.error(f"Update L–Q failed: {res}")
            except Exception as e:
                st.error(f"Failed to update L–Q via GAS: {e}")
