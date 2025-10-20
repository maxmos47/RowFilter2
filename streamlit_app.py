
# Patient Data — Edit Columns (Yes/No Form) → Show Updated Row (Dashboard Only)

import pandas as pd
import streamlit as st
import requests

DEFAULT_SHEET_ID = "1lKKAgJMcpIt2F6E2SJJJYCxybAV2l_Cli1Jb-LzlSkA"
DEFAULT_GID = "0"
DEFAULT_SHEET_CSV = f"https://docs.google.com/spreadsheets/d/{DEFAULT_SHEET_ID}/export?format=csv&gid={DEFAULT_GID}"

SUBMIT_ENDPOINT = st.secrets.get("SUBMIT_ENDPOINT", "")
SUBMIT_SECRET   = st.secrets.get("SUBMIT_SECRET", "")
TARGET_GID      = st.secrets.get("TARGET_GID", DEFAULT_GID)

def get_query() -> dict:
    try:
        return dict(st.query_params)
    except Exception:
        return {k:(v[0] if isinstance(v, list) else v) for k,v in st.experimental_get_query_params().items()}

def coerce_int(x, default=None):
    try: return int(str(x))
    except Exception: return default

@st.cache_data(show_spinner=False, ttl=120)
def load_csv(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    df.columns = [str(c) for c in df.columns]
    return df

def not_found(msg: str):
    st.error("❌ " + msg)
    st.stop()

q = get_query()
LOCKED = str(q.get("lock", "")).lower() in ("1","true","yes","on")
VIEW   = (q.get("view") or "").lower()

st.set_page_config(page_title="Patient data", layout="centered", initial_sidebar_state=("collapsed" if LOCKED else "auto"))

hide_css = "" if not LOCKED else "[data-testid='stSidebar'] {display:none !important;} [data-testid='collapsedControl'] {display:none !important;}"
css = '''
<style>
{HIDE}
.block-container {padding-top:.25rem; padding-bottom:1rem; max-width:840px;}
.kv-card {border:1px solid #e5e7eb; border-radius:.75rem; padding:.65rem .75rem; background:#fff;}
.small-cap { color:#6b7280; font-size:.85rem; margin-top:.5rem; }
</style>
'''.replace("{HIDE}", hide_css)
st.markdown(css, unsafe_allow_html=True)
st.subheader("Patient data")

if LOCKED:
    sheet_csv = DEFAULT_SHEET_CSV
else:
    sheet_csv = q.get("sheet") or DEFAULT_SHEET_CSV

try:
    df = load_csv(sheet_csv)
except Exception as e:
    not_found("โหลดข้อมูลจาก CSV ไม่สำเร็จ: " + str(e))

if df.empty:
    not_found("ตารางว่าง (No data rows)")

row_param = coerce_int(q.get("row"), None)
selected_idx = 0 if row_param is None else row_param - 1

def get_col_name_by_pos(df, pos):
    idx = pos - 1
    return df.columns[idx] if 0 <= idx < len(df.columns) else None

col_L = get_col_name_by_pos(df, 12)
col_M = get_col_name_by_pos(df, 13)
col_N = get_col_name_by_pos(df, 14)
if not all([col_L,col_M,col_N]): not_found("ชีตนี้ยังไม่มีคอลัมน์ L/M/N ครบ 3 คอลัมน์")

row = df.iloc[selected_idx]

YES_NO = ["Yes","No"]
def yn_index(v):
    t = str(v).strip().lower()
    return 0 if t in ("yes","y","true","1") else 1

def render_dashboard(dr):
    st.dataframe(dr.to_frame().T, use_container_width=True)
    st.markdown(f"<div class='small-cap'>Row {selected_idx+1} of {len(df)}</div>", unsafe_allow_html=True)

if VIEW != "dashboard":
    st.write("**อัปเดตค่า (ตอบได้เฉพาะ Yes / No)**")
    with st.form("edit_yesno", clear_on_submit=False):
        new_L = st.selectbox(col_L, YES_NO, index=yn_index(row[col_L]))
        new_M = st.selectbox(col_M, YES_NO, index=yn_index(row[col_M]))
        new_N = st.selectbox(col_N, YES_NO, index=yn_index(row[col_N]))
        submitted = st.form_submit_button("Submit")
    if submitted:
        if not SUBMIT_ENDPOINT or not SUBMIT_SECRET:
            not_found("ยังไม่ได้ตั้งค่า SUBMIT_ENDPOINT หรือ SUBMIT_SECRET")
        sheet_row = selected_idx + 2
        payload = {"secret":SUBMIT_SECRET,"gid":TARGET_GID,"sheet_row":sheet_row,"values":{"L":new_L,"M":new_M,"N":new_N}}
        try:
            r = requests.post(SUBMIT_ENDPOINT, json=payload, timeout=20)
            r.raise_for_status(); resp = r.json()
        except Exception as e:
            not_found("ส่งข้อมูลไม่สำเร็จ: " + str(e))
        if str(resp.get("status")).lower()!="ok":
            not_found("บันทึกข้อมูลไม่สำเร็จ: " + str(resp))
        st.cache_data.clear()
        st.query_params.update({"row":str(selected_idx+1),"lock":"1","view":"dashboard"})
        st.success("บันทึกสำเร็จ → กำลังแสดงผลรายการที่อัปเดต")
        st.rerun()

try:
    df_latest = load_csv(sheet_csv)
    render_dashboard(df_latest.iloc[selected_idx])
except Exception:
    render_dashboard(row)
