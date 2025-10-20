
# Patient Treatment Dashboard — A–K before submit, A–C + L–R after submit

import pandas as pd
import streamlit as st
import requests

DEFAULT_SHEET_ID = "1lKKAgJMcpIt2F6E2SJJJYCxybAV2l_Cli1Jb-LzlSkA"
DEFAULT_GID = "0"
DEFAULT_SHEET_CSV = f"https://docs.google.com/spreadsheets/d/{DEFAULT_SHEET_ID}/export?format=csv&gid={DEFAULT_GID}"

SUBMIT_ENDPOINT = st.secrets.get("SUBMIT_ENDPOINT", "")
SUBMIT_SECRET   = st.secrets.get("SUBMIT_SECRET", "")
TARGET_GID      = st.secrets.get("TARGET_GID", DEFAULT_GID)

def get_query():
    try:
        return dict(st.query_params)
    except Exception:
        return {k:(v[0] if isinstance(v,list) else v) for k,v in st.experimental_get_query_params().items()}

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

q = get_query()
LOCKED = str(q.get("lock","")).lower() in ("1","true","yes","on")
VIEW   = (q.get("view") or "").lower()

st.set_page_config(page_title="Patient Treatment", layout="centered", initial_sidebar_state=("collapsed" if LOCKED else "auto"))

hide_css = "" if not LOCKED else "[data-testid='stSidebar'] {display:none !important;} [data-testid='collapsedControl'] {display:none !important;}"
css = '''
<style>
{HIDE}
.block-container {padding-top:.5rem; padding-bottom:1rem; max-width:860px;}
.dataframe {font-size:14px !important;}
@media (max-width:600px) {
  .dataframe {font-size:12px !important;}
}
.small-cap { color:#6b7280; font-size:.85rem; margin-top:.5rem; }
</style>
'''.replace("{HIDE}", hide_css)
st.markdown(css, unsafe_allow_html=True)
st.subheader("Patient treatment")

if LOCKED: sheet_csv = DEFAULT_SHEET_CSV
else:
    sheet_csv = q.get("sheet") or DEFAULT_SHEET_CSV
    if not LOCKED:
        with st.sidebar:
            st.caption("Data source override")
            sheet_csv_in = st.text_input("Google Sheet CSV URL", value=sheet_csv)
            sheet_csv = sheet_csv_in or sheet_csv

try:
    df = load_csv(sheet_csv)
except Exception as e:
    not_found("โหลดข้อมูลจาก CSV ไม่สำเร็จ: " + str(e))
if df.empty: not_found("ไม่มีข้อมูลในชีต")

row_param = coerce_int(q.get("row"), None)
selected_idx = 0 if row_param is None else row_param - 1
if selected_idx < 0 or selected_idx >= len(df): not_found("Row out of range")

# define columns
cols_AK = df.columns[:11].tolist()
cols_AC = df.columns[:3].tolist()
cols_LR = df.columns[11:18].tolist()  # 12th–18th (L–R)

# identify L,M,N
def get_col(df,pos): 
    i=pos-1
    return df.columns[i] if 0<=i<len(df.columns) else None
col_L, col_M, col_N = get_col(df,12), get_col(df,13), get_col(df,14)

row = df.iloc[selected_idx]

YES_NO = ["Yes","No"]
def yn_index(v):
    return 0 if str(v).strip().lower() in ("yes","true","y","1") else 1

def render_table(dr, columns):
    subset = dr[columns] if all(c in dr.index for c in columns) else dr
    st.dataframe(subset.to_frame().T, use_container_width=True)

if VIEW != "dashboard":
    # show A–K first
    st.write("**Patient information (A–K)**")
    render_table(row, cols_AK)

    # form section
    st.write("**Patient treatment**")
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
            r=requests.post(SUBMIT_ENDPOINT,json=payload,timeout=20); r.raise_for_status(); resp=r.json()
        except Exception as e:
            not_found("ส่งข้อมูลไม่สำเร็จ: " + str(e))
        if str(resp.get("status")).lower()!="ok": not_found("บันทึกข้อมูลไม่สำเร็จ: " + str(resp))
        st.cache_data.clear()
        st.query_params.update({"row":str(selected_idx+1),"lock":"1","view":"dashboard"})
        st.success("บันทึกสำเร็จ → กำลังแสดงผล Dashboard")
        st.rerun()

else:
    # dashboard: A–C + L–R
    st.write("### Patient summary (A–C, L–R)")
    try:
        df2 = load_csv(sheet_csv)
        dr = df2.iloc[selected_idx]
        cols_show = [c for c in cols_AC+cols_LR if c in dr.index]
        render_table(dr, cols_show)
    except Exception:
        render_table(row, cols_AC+cols_LR)
