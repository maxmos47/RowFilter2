
# Patient Treatment — Card-grid v2 (Mobile-friendly)
# Patient Information uses the same kv-grid card layout before/after submit.

import pandas as pd
import streamlit as st
import requests

# ====== READ CONFIG ======
DEFAULT_SHEET_ID = "1lKKAgJMcpIt2F6E2SJJJYCxybAV2l_Cli1Jb-LzlSkA"
DEFAULT_GID = "0"
DEFAULT_SHEET_CSV = f"https://docs.google.com/spreadsheets/d/{DEFAULT_SHEET_ID}/export?format=csv&gid={DEFAULT_GID}"

# ====== WRITE CONFIG (Apps Script Web App) ======
SUBMIT_ENDPOINT = st.secrets.get("SUBMIT_ENDPOINT", "")
SUBMIT_SECRET   = st.secrets.get("SUBMIT_SECRET", "")
TARGET_GID      = st.secrets.get("TARGET_GID", DEFAULT_GID)

def get_query():
    try:
        return dict(st.query_params)
    except Exception:
        return {k:(v[0] if isinstance(v, list) else v) for k,v in st.experimental_get_query_params().items()}

def coerce_int(x, default=None):
    try: return int(str(x))
    except Exception: return default

@st.cache_data(show_spinner=False, ttl=120)
def load_csv(url):
    df = pd.read_csv(url)
    df.columns = [str(c) for c in df.columns]
    return df

def not_found(msg):
    st.error("❌ " + msg)
    st.stop()

q = get_query()
LOCKED = str(q.get("lock","")).lower() in ("1","true","yes","on")
VIEW   = (q.get("view") or "").lower()  # 'dashboard' after submit

st.set_page_config(page_title="Patient Treatment", layout="centered",
                   initial_sidebar_state=("collapsed" if LOCKED else "auto"))

# ====== CSS: kv-grid style (match user's sample) ======
hide_css = "" if not LOCKED else "[data-testid='stSidebar'] {display:none !important;} [data-testid='collapsedControl'] {display:none !important;}"
css = '''
<style>
{HIDE}
/* overall container */
.block-container {{ padding-top:.5rem; padding-bottom:1rem; max-width: 920px; }}

/* Card grid like user's file */
.kv-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}}
@media (max-width: 900px) {{
  .kv-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media (max-width: 580px) {{
  .kv-grid {{ grid-template-columns: 1fr; }}
}}

/* Card */
.kv-card {{
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,.06);
}}

/* Label & Value */
.kv-label {{
  font-size: 0.90rem;
  color: #6b7280;
  margin-bottom: 4px;
  line-height: 1.1;
}}
.kv-value {{
  font-size: 1.10rem;
  color: #111827;
  word-break: break-word;
  line-height: 1.3;
}}

/* Hide default Streamlit top header */
header[data-testid="stHeader"] {{ height:0; visibility: hidden; }}

.small-cap {{ color:#6b7280; font-size:.85rem; margin-top:.5rem; }}
</style>
'''.replace("{HIDE}", hide_css)
st.markdown(css, unsafe_allow_html=True)

def render_cards(row: pd.Series, columns: list, title: str):
    # Patient Information title (no extra "Patient treatment" heading on top page)
    st.markdown(f"### {title}")
    cards = []
    for c in columns:
        val = row.get(c, "")
        cards.append(
            f'<div class="kv-card">'
            f'<div class="kv-label">{c}</div>'
            f'<div class="kv-value">{val}</div>'
            f'</div>'
        )
    html = '<div class="kv-grid">' + "\n".join(cards) + '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ====== Determine data source ======
if LOCKED:
    sheet_csv = DEFAULT_SHEET_CSV
else:
    sheet_csv = q.get("sheet") or DEFAULT_SHEET_CSV
    if not LOCKED:
        with st.sidebar:
            st.caption("Data source (override)")
            sheet_csv = st.text_input("Google Sheet CSV URL", value=sheet_csv) or sheet_csv

# ====== Load data ======
try:
    df = load_csv(sheet_csv)
except Exception as e:
    not_found("โหลดข้อมูลจาก CSV ไม่สำเร็จ: " + str(e))
if df.empty: not_found("ไม่มีข้อมูลในชีต")

row_param = coerce_int(q.get("row"), None)
selected_idx = 0 if row_param is None else row_param - 1
if not (0 <= selected_idx < len(df)):
    not_found(f"Row out of range (1–{len(df)})")

# Column ranges (A–K, A–C, L–R)
cols_AK = df.columns[:11].tolist()       # A..K
cols_AC = df.columns[:3].tolist()        # A..C
cols_LR = df.columns[11:18].tolist()     # L..R (12th..18th)

# L/M/N column names by position (12/13/14)
def get_by_pos(df, pos):
    i = pos - 1
    return df.columns[i] if 0 <= i < len(df.columns) else None
col_L, col_M, col_N = get_by_pos(df,12), get_by_pos(df,13), get_by_pos(df,14)
if not all([col_L, col_M, col_N]):
    not_found("ชีตนี้ยังไม่มีคอลัมน์ L/M/N ครบ 3 คอลัมน์")

row = df.iloc[selected_idx]

# ====== Pre-submit view ======
if VIEW != "dashboard":
    # 1) Patient Information (A–K) as kv-grid cards
    render_cards(row, cols_AK, title="Patient information")

    # 2) Patient treatment form (Yes/No for L/M/N) — keep as is
    YES_NO = ["Yes", "No"]
    def yn_index(v):
        return 0 if str(v).strip().lower() in ("yes","true","y","1") else 1

    with st.form("treat_yesno_form", clear_on_submit=False):
        # Heading is allowed here (form section), previous "top heading" was removed already
        st.markdown("### Patient treatment")
        new_L = st.selectbox(col_L, YES_NO, index=yn_index(row[col_L]))
        new_M = st.selectbox(col_M, YES_NO, index=yn_index(row[col_M]))
        new_N = st.selectbox(col_N, YES_NO, index=yn_index(row[col_N]))
        submitted = st.form_submit_button("Submit")

    if submitted:
        if not SUBMIT_ENDPOINT or not SUBMIT_SECRET:
            not_found("ยังไม่ได้ตั้งค่า SUBMIT_ENDPOINT หรือ SUBMIT_SECRET")
        sheet_row = selected_idx + 2  # account for header row
        payload = {
            "secret": SUBMIT_SECRET,
            "gid": TARGET_GID,
            "sheet_row": sheet_row,
            "values": {"L": new_L, "M": new_M, "N": new_N}
        }
        try:
            r = requests.post(SUBMIT_ENDPOINT, json=payload, timeout=20)
            r.raise_for_status(); resp = r.json()
        except Exception as e:
            not_found("ส่งข้อมูลไม่สำเร็จ: " + str(e))
        if str(resp.get("status")).lower() != "ok":
            not_found("บันทึกข้อมูลไม่สำเร็จ: " + str(resp))

        # Reload to dashboard
        st.cache_data.clear()
        st.query_params.update({"row": str(selected_idx+1), "lock": "1", "view": "dashboard"})
        st.success("บันทึกสำเร็จ → กำลังแสดงผล Dashboard")
        st.rerun()

# ====== Post-submit view (Dashboard) ======
else:
    # Patient Information as cards (A–C + L–R), same kv-grid layout, no "A–C + L–R" text shown
    try:
        df2 = load_csv(sheet_csv)
        dr = df2.iloc[selected_idx]
    except Exception:
        dr = row
    columns_show = [c for c in (cols_AC + cols_LR) if c in dr.index]
    render_cards(dr, columns_show, title="Patient information")
