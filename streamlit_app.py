# Minimal Patient Data Viewer (Mobile-Friendly) — FIXED (Duplicated)
# ------------------------------------------------
# URL params: ?row=, ?id=&id_col=, optional ?lock=1
# - In lock mode, sidebar is hidden and sheet override is disabled.
# - Only a single, large table is shown.

import json
import pandas as pd
import numpy as np
import streamlit as st

from urllib.parse import urlencode

def get_query_params() -> dict:
    try:
        return dict(st.query_params)
    except Exception:
        return {k: v[0] if isinstance(v, list) else v for k, v in st.experimental_get_query_params().items()}

def coerce_int(x, default=None):
    try:
        return int(str(x))
    except Exception:
        return default

@st.cache_data(show_spinner=False, ttl=300)
def load_csv(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    df.columns = [str(c) for c in df.columns]
    return df

# --- Page config & CSS for mobile-friendly table ---
q_pre = get_query_params()
LOCKED = str(q_pre.get("lock", "")).lower() in ("1", "true", "yes", "on")

st.set_page_config(page_title="Patient data", layout="centered", initial_sidebar_state=("collapsed" if LOCKED else "auto"))

hide_css = "" if not LOCKED else '''
[data-testid='stSidebar'] {display:none !important;}
[data-testid='collapsedControl'] {display:none !important;}
'''
st.markdown(
    '''
    <style>
      %HIDE%
      .block-container {padding-top: 0.5rem; padding-bottom: 1.25rem; max-width: 1200px;}
      .stDataFrame table {font-size: 1.05rem;}
      .stDataFrame [data-testid="stHorizontalBlock"] {overflow-x: auto;}
      header[data-testid="stHeader"] {height: 0; visibility: hidden;}
    </style>
    '''.replace("%HIDE%", hide_css),
    unsafe_allow_html=True,
)

# No big title per requirement, only a small section label
st.subheader("Patient data")

# --- Determine sheet source ---
DEFAULT_SHEET = "https://docs.google.com/spreadsheets/d/1lKKAgJMcpIt2F6E2SJJJYCxybAV2l_Cli1Jb-LzlSkA/export?format=csv&gid=0"
if LOCKED:
    sheet = DEFAULT_SHEET
else:
    q_sheet = q_pre.get("sheet")
    sheet = q_sheet or DEFAULT_SHEET
    # Optional builder via sheet_id/gid
    sid = q_pre.get("sheet_id")
    gid = q_pre.get("gid")
    if not q_sheet and sid:
        gid_val = gid if gid is not None else "0"
        sheet = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid_val}"

# Sidebar only in non-locked mode (kept for manual override if needed)
if not LOCKED:
    with st.sidebar:
        st.caption("Data source (optional override)")
        csv_url = st.text_input("Google Sheet CSV URL", value=sheet, placeholder="https://...export?format=csv&gid=0")
else:
    csv_url = sheet

# --- Load data ---
try:
    df = load_csv(csv_url)
except Exception as e:
    st.error(f"โหลดข้อมูลจาก CSV ไม่สำเร็จ: {e}")
    st.stop()

if df.empty:
    st.warning("ตารางว่าง (No data rows).")
    st.stop()

# --- Resolve target row from URL ---
q = q_pre
row_param = coerce_int(q.get("row"), default=None)
id_value = q.get("id")
id_col = q.get("id_col")

selected_idx = None
if id_value and id_col and id_col in df.columns:
    matches = df.index[df[id_col].astype(str) == str(id_value)].tolist()
    if matches:
        selected_idx = matches[0]
elif row_param is not None:
    base = max(1, row_param)
    base = min(base, len(df))
    selected_idx = base - 1
else:
    if LOCKED:
        st.error("Locked mode ต้องระบุพารามิเตอร์ ?row= หรือ ?id= & id_col=")
        st.stop()
    selected_idx = 0

selected_idx = max(0, min(selected_idx, len(df) - 1))

# --- Show only the table (transpose for readability) ---
row = df.iloc[selected_idx]
st.dataframe(row.to_frame().T, use_container_width=True, height=420)

# Tiny info (no actions/metrics/navigation)
st.caption(f"Showing row {selected_idx+1} of {len(df)}")
