# Patient Data — Streamlit x Google Apps Script (Treatment L–Q Yes/No)
# -------------------------------------------------
# Changes per request:
# • Remove the A–K summary block entirely.
# • Rename the editor UI to "Treatment" (both unlocked and locked modes).
# • Write back to Google Sheets via Google Apps Script Web App (HTTP), not gspread.
#
# Usage
# - Provide the CSV export URL of your Google Sheet via ?sheet=... (or edit DEFAULT_SHEET_CSV).
# - Provide the GAS Web App URL via secrets: st.secrets["gas_url"]  (or via query param ?gas=... in unlocked mode).
# - Select row with ?row=1 (or use id & id_col).
# - After Submit, the app reloads with lock=1 and shows the updated dashboard.
#
# Notes
# - L..Q correspond to columns 12..17 (0-based index 11..16). We POST 6 values to GAS.
import re
import pandas as pd
import requests
import streamlit as st

DEFAULT_SHEET_CSV = "https://docs.google.com/spreadsheets/d/1lKKAgJMcpIt2F6E2SJJJYCxybAV2l_Cli1Jb-LzlSkA/export?format=csv&gid=0"

# ---------------- Utils ----------------

def get_query_params() -> dict:
    try:
        return dict(st.query_params)
    except Exception:
        return {k: v[0] if isinstance(v, list) else v for k, v in st.experimental_get_query_params().items()}

def set_query_params(**kwargs):
    try:
        st.query_params.update(kwargs)
    except Exception:
        st.experimental_set_query_params(**{**get_query_params(), **kwargs})

def coerce_int(x, default=None):
    try:
        return int(str(x))
    except Exception:
        return default

def looks_like_image_url(x: str) -> bool:
    if not isinstance(x, str):
        return False
    return bool(re.search(r"\.(png|jpg|jpeg|gif|webp)(\?.*)?$", x, re.IGNORECASE))

@st.cache_data(show_spinner=False, ttl=300)
def load_csv(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    df.columns = [str(c) for c in df.columns]
    return df

def gas_update_lq(gas_url: str, rownum: int, values_yes_no):
    """POST to GAS Web App to update columns L..Q for the given 1-based row."""
    payload = {"row": int(rownum), "values": list(values_yes_no)}
    r = requests.post(gas_url, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()

def gas_get_lq(gas_url: str, rownum: int):
    """GET current L..Q for the given row, if you want immediate consistency."""
    r = requests.get(gas_url, params={"row": int(rownum)}, timeout=20)
    r.raise_for_status()
    return r.json()

# --------------- Page setup ---------------
q_pre = get_query_params()
LOCKED = str(q_pre.get("lock", "")).lower() in ("1", "true", "yes", "on")
st.set_page_config(page_title="Patient data", layout="centered", initial_sidebar_state=("collapsed" if LOCKED else "auto"))

hide_css = "" if not LOCKED else """
[data-testid='stSidebar'] {display:none !important;}
[data-testid='collapsedControl'] {display:none !important;}
"""

st.markdown(
    """
    <style>
      {hide_css}
      .block-container {{padding-top: .25rem; padding-bottom: 1rem; max-width: 760px;}}
      .kv-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: .55rem; }}
      @media (max-width: 520px) {{ .kv-grid {{ grid-template-columns: 1fr; }} }}
      .kv-card {{ border: 1px solid #e5e7eb; border-radius: .75rem; padding: .65rem .75rem; background: #ffffff; box-shadow: 0 1px 2px rgba(0,0,0,.04); }}
      .kv-label {{ font-size: .82rem; color: #6b7280; margin-bottom: .25rem; line-height: 1.1; }}
      .kv-value {{ font-size: 1.05rem; color: #111827; word-break: break-word; white-space: pre-wrap; line-height: 1.25; }}
      .kv-img {{ width: 100%; height: auto; border-radius: .5rem; }}
      header[data-testid="stHeader"] {{height: 0; visibility: hidden;}}
      .small-cap {{ color:#6b7280; font-size:.85rem; margin-top:.5rem; }}
      .muted {{ color: #6b7280; font-size: .9rem; }}
    </style>
    """.format(hide_css=hide_css),
    unsafe_allow_html=True,
)

st.subheader("Patient data")

# --- Determine data source & GAS URL ---
if LOCKED:
    sheet_csv = DEFAULT_SHEET_CSV
else:
    sheet_csv = q_pre.get("sheet") or DEFAULT_SHEET_CSV

gas_url = st.secrets.get("gas_url") or q_pre.get("gas")

if not LOCKED:
    with st.sidebar:
        st.caption("Data/API settings")
        sheet_csv_input = st.text_input(
            "Google Sheet CSV URL",
            value=sheet_csv,
            placeholder="https://.../export?format=csv&gid=0"
        )
        gas_url_input = st.text_input(
            "Google Apps Script Web App URL (exec)",
            value=gas_url or "",
            placeholder="https://script.google.com/macros/s/XXXXX/exec"
        )
        sheet_csv = sheet_csv_input or sheet_csv
        gas_url = gas_url_input or gas_url

# --- Load data ---
try:
    df = load_csv(sheet_csv)
except Exception as e:
    st.error(f"โหลดข้อมูลจาก CSV ไม่สำเร็จ: {e}")
    st.stop()

if df.empty:
    st.warning("ตารางว่าง (No data rows).")
    st.stop()

# --- Resolve target row / id ---
q = q_pre
row_param = coerce_int(q.get("row"), default=None)
id_value = q.get("id")
id_col = q.get("id_col")

selected_idx = None
if id_value or id_col:
    if not (id_value and id_col):
        st.error("❌ ไม่พบข้อมูล: โปรดระบุทั้ง id= และ id_col=")
        st.stop()
    if id_col not in df.columns:
        st.error(f"❌ ไม่พบคอลัมน์ '{id_col}' ในข้อมูล")
        st.stop()
    matches = df.index[df[id_col].astype(str) == str(id_value)].tolist()
    if matches:
        selected_idx = matches[0]
    else:
        st.error("❌ ไม่พบข้อมูลตาม ID ที่ระบุ")
        st.stop()
elif row_param is not None:
    if 1 <= row_param <= len(df):
        selected_idx = row_param - 1
    else:
        st.error(f"❌ ไม่พบข้อมูลในแถวที่ระบุ (row={row_param}) ข้อมูลมีช่วง 1–{len(df)})")
        st.stop()
else:
    if LOCKED:
        st.error("Locked mode ต้องระบุพารามิเตอร์ ?row= หรือ ?id= & id_col=")
        st.stop()
    selected_idx = 0

row = df.iloc[selected_idx]

# Helpers to render dashboard cards
priority = [c for c in ["HN","PatientID","Name","FullName","Triage","TriageScore","Age","Sex","VisitDate","ChiefComplaint","WaitingTime","Disposition"] if c in df.columns]
others = [c for c in df.columns if c not in priority]
ordered_cols = priority + others

def escape_html(s: str) -> str:
    return (s.replace("&","&amp;")
             .replace("<","&lt;")
             .replace(">","&gt;"))

def render_cards(ordered_cols):
    cards = []
    for col in ordered_cols:
        val = row[col]
        disp = "" if pd.isna(val) else str(val)
        if looks_like_image_url(disp):
            content = f"<img class='kv-img' src='{disp}' alt='{col}'>"
        else:
            content = escape_html(disp)
        cards.append(
            "<div class='kv-card'>"
            f"<div class='kv-label'>{escape_html(str(col))}</div>"
            f"<div class='kv-value'>{content}</div>"
            "</div>"
        )
    grid_html = "<div class='kv-grid'>" + "\n".join(cards) + "</div>"
    st.markdown(grid_html, unsafe_allow_html=True)
    st.markdown(f"<div class='small-cap'>Showing row {selected_idx+1} of {len(df)}</div>", unsafe_allow_html=True)

# ---------------- Locked (read-only) view WITH inline "Treatment" edit ----------------
if LOCKED:
    render_cards(ordered_cols)

    with st.expander("Treatment", expanded=False):
        lq_cols_locked = list(df.columns[11:17])  # L..Q
        if len(lq_cols_locked) < 6:
            st.info("ตารางนี้มีคอลัมน์ไม่ถึง Q — จะแสดงเท่าที่มี")
        yes_no_options = ("Yes", "No")
        default_vals = []
        for c in lq_cols_locked:
            raw = row[c]
            default_vals.append("Yes" if str(raw).strip().lower() == "yes" else "No")

        with st.form("edit_lq_locked_form", clear_on_submit=False):
            edits = []
            for i, c in enumerate(lq_cols_locked):
                sel = st.selectbox(
                    f"{c} (Col {chr(76+i)})",
                    yes_no_options,
                    index=0 if default_vals[i] == "Yes" else 1,
                    key=f"lq_locked_{i}"
                )
                edits.append(sel)
            submit_locked = st.form_submit_button("Submit (บันทึกการเปลี่ยนแปลง)")

        if submit_locked:
            if not gas_url:
                st.error("ยังไม่ได้ตั้งค่า Google Apps Script Web App URL (gas_url)")
                st.stop()
            try:
                sheet_rownum = selected_idx + 2  # 1-based (with header)
                values_to_write = list(edits) + [""] * (6 - len(edits))
                res = gas_update_lq(gas_url, rownum=sheet_rownum, values_yes_no=values_to_write[:6])
                st.success(f"บันทึกข้อมูลเรียบร้อย: {res.get('status', 'ok')}")
                set_query_params(**{**q_pre, "lock": "1"})
                st.rerun()
            except Exception as e:
                st.error(f"บันทึกไม่สำเร็จ: {e}")

    st.stop()

# ---------------- Unlocked: DIRECT Treatment Form (no A–K preview) --------
lq_cols = list(df.columns[11:17])  # L..Q are columns 12..17 (0-based 11..16)
if len(lq_cols) < 6:
    st.info("ตารางนี้มีคอลัมน์ไม่ถึง Q — จะแสดงเท่าที่มี")

with st.form("edit_lq_form", clear_on_submit=False):
    st.markdown("### Treatment")
    yes_no_options = ("Yes", "No")
    current_vals = []
    for i, c in enumerate(lq_cols):
        raw = row[c]
        default = "Yes" if str(raw).strip().lower() == "yes" else "No"
        sel = st.selectbox(f"{c} (Col {chr(76+i)})", yes_no_options, index=0 if default=="Yes" else 1, key=f"lq_{i}")
        current_vals.append(sel)

    submitted = st.form_submit_button("Submit (บันทึกการเปลี่ยนแปลง)")

if submitted:
    if not gas_url:
        st.error("ยังไม่ได้ตั้งค่า Google Apps Script Web App URL (gas_url)")
        st.stop()
    try:
        sheet_rownum = selected_idx + 2
        values_to_write = list(current_vals) + [""] * (6 - len(current_vals))
        res = gas_update_lq(gas_url, rownum=sheet_rownum, values_yes_no=values_to_write[:6])
        st.success("บันทึกข้อมูลเรียบร้อย → กำลังโหลดแดชบอร์ดแบบล็อก")
        set_query_params(**{**q_pre, "lock": "1"})
        st.rerun()
    except Exception as e:
        st.error(f"บันทึกไม่สำเร็จ: {e}")

# Reference: show the full row (for context)
st.markdown("---")
st.markdown("**ข้อมูลทั้งหมดของแถวนี้**")
render_cards(ordered_cols)
