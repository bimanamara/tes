
import streamlit as st, pandas as pd
from pathlib import Path

SCHEMAS = {
    "hor_events.csv": ["event_id","name","description","severity"],
    "hor_agents.csv": ["agent_id","name","occurrence"],
    "hor_actions.csv": ["action_id","name","difficulty","cost","manhours"],
    "respondents.csv": ["respondent_id","name","role","weight"],
    "criteria.csv": ["criterion_id","name"],
    "subcriteria.csv": ["sub_id","name","criterion_id"],
    "dematel_edges.csv": ["respondent_id","from_sub","to_sub","score"],
    "suppliers.csv": ["supplier_id","name","region"],
    "supplier_ratings.csv": ["supplier_id","sub_id","respondent_id","rating","plant_id","time_period","cheese_type"],
    "allocation_plants.csv": ["plant_id","demand"],
    "allocation_suppliers.csv": ["supplier_id","capacity","unit_cost","quality_score"],
}

def map_columns_ui(tpl_dir: Path):
    st.subheader("Column Mapper (optional)")
    fname = st.selectbox(
    "Pilih file untuk remap kolom",
    sorted(SCHEMAS.keys()),
    key="basic_mapper_file"   # << key unik untuk mapper basic
)
    p = tpl_dir/fname
    if not p.exists():
        st.warning("File belum ada. Upload dulu lewat uploader di atas, atau generate dummy data.")
        return
    df = pd.read_csv(p)
    st.caption(f"Kolom saat ini: {list(df.columns)}")
    req = SCHEMAS[fname]
    # build mapping selections
    mapping = {}
    cols = ["<skip>"] + list(df.columns)
    st.write("Map kolom di file → ke skema standar berikut:")
    for k in req:
        mapping[k] = st.selectbox(f"{k}", cols, index=(cols.index(k) if k in cols else 0), key=f"map_{fname}_{k}")
    if st.button("Apply Mapping & Save", key=f"apply_{fname}"):
        # rename per mapping (skip ignored)
        rename = {v:k for k,v in mapping.items() if v in df.columns}
        df2 = df.rename(columns=rename)
        # ensure required columns exist
        for k in req:
            if k not in df2.columns:
                df2[k] = None
        # reorder
        df2 = df2[req + [c for c in df2.columns if c not in req]]
        df2.to_csv(p, index=False)
        st.success(f"Mapping applied & saved to {fname}.")
        st.dataframe(df2.head())
