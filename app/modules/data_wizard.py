
import streamlit as st, pandas as pd, io
from pathlib import Path
REQ_FILES = [
    'hor_events.csv','hor_agents.csv','hor_R.csv',
    'hor_actions.csv','hor_effectiveness.csv',
    'respondents.csv','criteria.csv','subcriteria.csv','dematel_edges.csv',
    'suppliers.csv','supplier_ratings.csv'
]
def wizard(tpl_dir: Path, out_dir: Path):
    st.subheader("Upload & Validate CSV")
    upl = st.file_uploader("Upload multiple CSV files", type=['csv'], accept_multiple_files=True)
    if upl:
        reports = []
        for f in upl:
            try:
                df = pd.read_csv(f)
                (tpl_dir/f.name).write_bytes(f.getbuffer())
                reports.append(dict(file=f.name, rows=len(df), cols=len(df.columns), status="OK"))
            except Exception as e:
                reports.append(dict(file=f.name, rows=0, cols=0, status=f"ERROR: {e}"))
        st.dataframe(pd.DataFrame(reports))
        st.success("File tersimpan. Jalankan ulang tab analisis untuk melihat data baru.")
    miss = [f for f in REQ_FILES if not (tpl_dir/f).exists()]
    if miss:
        st.warning("File template yang *belum ada*: " + ", ".join(miss))
