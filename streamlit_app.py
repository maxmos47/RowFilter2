
# Patient Treatment — Card-grid v3 (L–Q form, A–C + R–U dashboard)

import pandas as pd
import streamlit as st
import requests

# ===== READ CONFIG =====
DEFAULT_SHEET_ID = "1lKKAgJMcpIt2F6E2SJJJYCxybAV2l_Cli1Jb-LzlSkA"
DEFAULT_GID = "0"
DEFAULT_SHEET_CSV = f"https://docs.google.com/spreadsheets/d/{DEFAULT_SHEET_ID}/export?format=csv&gid={DEFAULT_GID}"

# ===== WRITE CONFIG =====
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
    st.error("❌ " + msg); st.stop()

# ===== Page / CSS =====
q = get_query()
LOCKED = str(q.get("lock","")).lower() in ("1","true","yes","on")
VIEW   = (q.get("view") or "").lower()

st.set_page_config(page_title="Patient Treatment", layout="centered",
                   initial_sidebar_state=("collapsed" if LOCKED else "auto"))

hide_css = "" if not LOCKED else "[data-testid='stSidebar'] {display:none !important;} [data-testid='collapsedControl'] {display:none !important;}"
css = '''
<style>
{HIDE}
.block-container {{ padding-top:.5rem; padding-bottom:1rem; max-width: 940px; }}
/* Card-grid styling (improved sizing for mobile) */
.kv-grid {{ display:grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }}
@media (max-width: 900px) {{ .kv-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
@media (max-width: 580px) {{ .kv-grid {{ grid-template-columns: 1fr; }} }}
.kv-card {{ background:#fff; border:1px solid #e5e7eb; border-radius:14px; padding:14px 16px;
           box-shadow:0 1px 3px rgba(0,0,0,.06);}}
.kv-label {{ font-size:0.95rem; color:#6b7280; margin-bottom:4px; line-height:1.15; }}
.kv-value {{ font-size:1.15rem; color:#111827; line-height:1.35; word-break:break-word; }}
/* Reduce Streamlit header */
header[data-testid="stHeader"] {{ height:0; visibility:hidden; }}
.section-title {{ font-size:1.15rem; font-weight:600; margin: .75rem 0 .25rem 0; }}
.hr {{ height:1px; background:#e5e7eb; margin:.5rem 0 1rem 0; }}
</style>
'''.replace("{HIDE}", hide_css)
st.markdown(css, unsafe_allow_html=True)

def render_cards(row: pd.Series, columns: list, title: str):
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    cards = []
    for c in columns:
        val = row.get(c, "")
        cards.append(
            f"<div class='kv-card'><div class='kv-label'>{c}</div>"
            f"<div class='kv-value'>{val}</div></div>"
        )
    st.markdown("<div class='kv-grid'>" + "\n".join(cards) + "</div>", unsafe_allow_html=True)

# ===== Resolve data source =====
if LOCKED:
    sheet_csv = DEFAULT_SHEET_CSV
else:
    sheet_csv = q.get("sheet") or DEFAULT_SHEET_CSV
    if not LOCKED:
        with st.sidebar:
            st.caption("Data source (override)")
            sheet_csv = st.text_input("Google Sheet CSV URL", value=sheet_csv) or sheet_csv

# ===== Load data =====
try:
    df = load_csv(sheet_csv)
except Exception as e:
    not_found("โหลดข้อมูลจาก CSV ไม่สำเร็จ: " + str(e))
if df.empty:
    not_found("ไม่มีข้อมูลในชีต")

row_param = coerce_int(q.get("row"), None)
selected_idx = 0 if row_param is None else row_param - 1
if not (0 <= selected_idx < len(df)):
    not_found(f"Row out of range (1–{len(df)})")

# Column ranges
cols_AK = df.columns[:11].tolist()       # A..K
cols_AC = df.columns[:3].tolist()        # A..C
cols_RU = df.columns[17:21].tolist()     # R..U  (18..21)

# L..Q positions (12..17)
def by_pos(df, pos):
    i = pos - 1
    return df.columns[i] if 0 <= i < len(df.columns) else None

col_names_LQ = [by_pos(df, p) for p in range(12, 18)]
if not all(col_names_LQ):
    not_found("ชีตนี้ยังไม่มีคอลัมน์ครบถึง Q (อย่างน้อยต้องถึงคอลัมน์ Q)")

row = df.iloc[selected_idx]

# ===== BEFORE SUBMIT =====
if VIEW != "dashboard":
    # Patient information (A–K) as cards
    render_cards(row, cols_AK, title="Patient information")

    # Patient treatment form (L–Q) — Yes/No
    st.markdown("<div class='section-title'>Patient treatment</div>", unsafe_allow_html=True)
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    YES_NO = ["Yes", "No"]
    def yn_index(v):
        return 0 if str(v).strip().lower() in ("yes","true","y","1") else 1

    with st.form("treat_yesno_LQ", clear_on_submit=False):
        new_vals = {}
        for name in col_names_LQ:
            current = row.get(name, "")
            new_vals[name] = st.selectbox(name, YES_NO, index=yn_index(current))
        submitted = st.form_submit_button("Submit")

    if submitted:
        if not SUBMIT_ENDPOINT or not SUBMIT_SECRET:
            not_found("ยังไม่ได้ตั้งค่า SUBMIT_ENDPOINT หรือ SUBMIT_SECRET")

        # Build {L..Q} keys for backend
        letters = ["L","M","N","O","P","Q"]
        payload_values = {}
        for i, col_name in enumerate(col_names_LQ):
            payload_values[letters[i]] = new_vals[col_name]

        sheet_row = selected_idx + 2
        payload = {
            "secret": SUBMIT_SECRET,
            "gid": TARGET_GID,
            "sheet_row": sheet_row,
            "values": payload_values
        }
        try:
            r = requests.post(SUBMIT_ENDPOINT, json=payload, timeout=20)
            r.raise_for_status(); resp = r.json()
        except Exception as e:
            not_found("ส่งข้อมูลไม่สำเร็จ: " + str(e))
        if str(resp.get("status")).lower() != "ok":
            not_found("บันทึกข้อมูลไม่สำเร็จ: " + str(resp))

        st.cache_data.clear()
        st.query_params.update({"row": str(selected_idx+1), "lock": "1", "view": "dashboard"})
        st.success("บันทึกสำเร็จ → กำลังแสดงผล Dashboard")
        st.rerun()

# ===== AFTER SUBMIT (Dashboard) =====
else:
    try:
        df2 = load_csv(sheet_csv)
        dr = df2.iloc[selected_idx]
    except Exception:
        dr = row
    cols_show = [c for c in (cols_AC + cols_RU) if c in dr.index]
    render_cards(dr, cols_show, title="Patient information")
