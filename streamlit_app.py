
# Patient Data — Edit L/M/N via Form → Show Updated Row (Mobile-First)

import pandas as pd
import streamlit as st
import requests

# ========= CONFIG (READ) =========
DEFAULT_SHEET_ID = "1lKKAgJMcpIt2F6E2SJJJYCxybAV2l_Cli1Jb-LzlSkA"
DEFAULT_GID = "0"
DEFAULT_SHEET_CSV = f"https://docs.google.com/spreadsheets/d/{DEFAULT_SHEET_ID}/export?format=csv&gid={DEFAULT_GID}"

# ========= CONFIG (WRITE) via Apps Script Web App =========
SUBMIT_ENDPOINT = st.secrets.get("SUBMIT_ENDPOINT", "")  # e.g. https://script.google.com/macros/s/AKfycb.../exec
SUBMIT_SECRET   = st.secrets.get("SUBMIT_SECRET", "")    # must match SECRET in Apps Script
TARGET_GID      = st.secrets.get("TARGET_GID", DEFAULT_GID)  # target tab gid to update

# ===== Helpers =====
def get_query() -> dict:
    try:
        return dict(st.query_params)
    except Exception:
        return {k:(v[0] if isinstance(v, list) else v) for k,v in st.experimental_get_query_params().items()}

def coerce_int(x, default=None):
    try:
        return int(str(x))
    except Exception:
        return default

@st.cache_data(show_spinner=False, ttl=120)
def load_csv(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    df.columns = [str(c) for c in df.columns]
    return df

def not_found(msg: str):
    st.error("❌ " + msg)
    st.stop()

# ===== Page & CSS =====
q = get_query()
LOCKED = str(q.get("lock", "")).lower() in ("1", "true", "yes", "on")
st.set_page_config(page_title="Patient data", layout="centered", initial_sidebar_state=("collapsed" if LOCKED else "auto"))

hide_css = "" if not LOCKED else "[data-testid='stSidebar'] {display:none !important;} [data-testid='collapsedControl'] {display:none !important;}"
css = '''
<style>
{HIDE}
.block-container {padding-top:.25rem; padding-bottom:1rem; max-width:840px;}
.kv-grid { display:grid; grid-template-columns:1fr 1fr; gap:.55rem; }
@media (max-width:560px) { .kv-grid { grid-template-columns:1fr; } }
.kv-card { border:1px solid #e5e7eb; border-radius:.75rem; padding:.65rem .75rem; background:#fff; box-shadow:0 1px 2px rgba(0,0,0,.04); }
.kv-label { font-size:.82rem; color:#6b7280; margin-bottom:.25rem; line-height:1.1; }
.kv-value { font-size:1.05rem; color:#111827; word-break:break-word; white-space:pre-wrap; line-height:1.25; }
header[data-testid="stHeader"] {height:0; visibility:hidden;}
.small-cap { color:#6b7280; font-size:.85rem; margin-top:.5rem; }
</style>
'''.replace("{HIDE}", hide_css)
st.markdown(css, unsafe_allow_html=True)

st.subheader("Patient data")

# ===== Determine data source (READ) =====
if LOCKED:
    sheet_csv = DEFAULT_SHEET_CSV
else:
    sheet_csv = q.get("sheet") or DEFAULT_SHEET_CSV
    sid = q.get("sheet_id")
    gid = q.get("gid")
    if (not q.get("sheet")) and sid:
        gid_val = gid if gid is not None else "0"
        sheet_csv = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid_val}"

if not LOCKED:
    with st.sidebar:
        st.caption("Data source (override)")
        sheet_csv_in = st.text_input("Google Sheet CSV URL", value=sheet_csv)
        sheet_csv = sheet_csv_in or sheet_csv

# ===== Load data =====
try:
    df = load_csv(sheet_csv)
except Exception as e:
    not_found("โหลดข้อมูลจาก CSV ไม่สำเร็จ: " + str(e))

if df.empty:
    not_found("ตารางว่าง (No data rows)")

# ===== Resolve target row =====
row_param = coerce_int(q.get("row"), None)
id_value  = q.get("id")
id_col    = q.get("id_col")

selected_idx = None
if id_value or id_col:
    if not (id_value and id_col):
        not_found("โปรดระบุให้ครบทั้ง id= และ id_col=")
    if id_col not in df.columns:
        not_found("ไม่พบคอลัมน์ '" + str(id_col) + "' ในข้อมูล")
    matches = df.index[df[id_col].astype(str) == str(id_value)].tolist()
    if not matches:
        not_found("ไม่พบข้อมูลตาม ID ที่ระบุ")
    selected_idx = matches[0]
elif row_param is not None:
    if 1 <= row_param <= len(df):
        selected_idx = row_param - 1
    else:
        not_found(f"ไม่พบข้อมูลในแถว (row={row_param}) ช่วงข้อมูล 1–{len(df)}")
else:
    selected_idx = 0

# ===== Column mapping for L/M/N =====
def get_col_name_by_pos(df: pd.DataFrame, pos_1based: int) -> str:
    idx = pos_1based - 1
    if idx < 0 or idx >= len(df.columns):
        return None
    return df.columns[idx]

col_L = get_col_name_by_pos(df, 12)
col_M = get_col_name_by_pos(df, 13)
col_N = get_col_name_by_pos(df, 14)
if not all([col_L, col_M, col_N]):
    not_found("ชีตนี้ยังไม่มีคอลัมน์ L/M/N ครบ 3 คอลัมน์")

row = df.iloc[selected_idx]
val_L = "" if pd.isna(row[col_L]) else str(row[col_L])
val_M = "" if pd.isna(row[col_M]) else str(row[col_M])
val_N = "" if pd.isna(row[col_N]) else str(row[col_N])

# ===== Form to edit L/M/N =====
st.write("**แก้ไขค่าคอลัมน์ L / M / N**")
with st.form("edit_lmn", clear_on_submit=False):
    new_L = st.text_input("L (" + col_L + ")", value=val_L)
    new_M = st.text_input("M (" + col_M + ")", value=val_M)
    new_N = st.text_input("N (" + col_N + ")", value=val_N)
    submitted = st.form_submit_button("Submit")

if submitted:
    if not SUBMIT_ENDPOINT:
        not_found("ยังไม่ได้ตั้งค่า SUBMIT_ENDPOINT ใน secrets")
    if not SUBMIT_SECRET:
        not_found("ยังไม่ได้ตั้งค่า SUBMIT_SECRET ใน secrets")

    sheet_row = selected_idx + 2  # 1 header row
    payload = {
        "secret": SUBMIT_SECRET,
        "gid": TARGET_GID,
        "sheet_row": sheet_row,
        "values": {"L": new_L, "M": new_M, "N": new_N}
    }
    try:
        r = requests.post(SUBMIT_ENDPOINT, json=payload, timeout=20)
        r.raise_for_status()
        resp = r.json()
    except Exception as e:
        not_found("ส่งข้อมูลไม่สำเร็จ: " + str(e))

    if str(resp.get("status")).lower() != "ok":
        not_found("บันทึกข้อมูลไม่สำเร็จ: " + str(resp))

    st.success("บันทึกสำเร็จ! กำลังโหลดข้อมูลแถวที่แก้ไขแล้ว")
    st.cache_data.clear()
    df = load_csv(sheet_csv)

    if sheet_row - 2 < len(df):
        updated = df.iloc[sheet_row - 2].to_frame().T
    else:
        updated = row.copy()
        updated[col_L] = new_L; updated[col_M] = new_M; updated[col_N] = new_N
        updated = updated.to_frame().T

    st.write("### แถวที่อัปเดตแล้ว")
    st.dataframe(updated, use_container_width=True)
else:
    st.write("### แถวปัจจุบัน")
    st.dataframe(row.to_frame().T, use_container_width=True)

st.caption(f"Target row {selected_idx+1} of {len(df)} — editing columns L/M/N")
