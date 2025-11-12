
import streamlit as st, pandas as pd, plotly.express as px, plotly.graph_objects as go

def supplier_profile_view(ranking, agg, gw, suppliers, ratings, subcriteria, criteria):
    if ranking is None or len(ranking)==0:
        st.info("Tidak ada supplier untuk ditampilkan.")
        return
    supp_ids = ranking['supplier_id'].tolist()
    sel = st.selectbox("Pilih supplier", supp_ids)
    st.write("Detail:", sel)
    # Contributions per subcriteria (agg is supplier×sub_id with respondent weights already)
    if agg is None or agg.empty or sel not in agg.index:
        st.info("Tidak ada agregasi subkriteria untuk supplier ini.")
        return
    contrib = agg.loc[sel].reindex(gw.index, fill_value=0) * gw
    contrib = contrib.sort_values(ascending=False)
    st.plotly_chart(px.bar(x=contrib.index, y=contrib.values, labels={'x':'Subcriteria','y':'Contribution'}, title="Kontribusi per Subcriteria"), use_container_width=True)

    # Group to criteria
    if 'criterion_id' in subcriteria.columns:
        map_sc = dict(zip(subcriteria['sub_id'], subcriteria['criterion_id']))
        crit_series = contrib.groupby(contrib.index.map(map_sc)).sum().sort_values(ascending=False)
        st.plotly_chart(px.bar(x=crit_series.index, y=crit_series.values, labels={'x':'Criteria','y':'Contribution'}, title="Kontribusi per Criteria"), use_container_width=True)

    # Time trend
    if ratings is not None and not ratings.empty and 'time_period' in ratings.columns:
        rt = ratings[ratings['supplier_id']==sel]
        if len(rt)>0:
            g = rt.groupby('time_period')['rating'].mean().sort_index()
            st.plotly_chart(px.line(x=g.index, y=g.values, labels={'x':'Periode','y':'Avg Rating'}, title="Tren Rating dari Waktu ke Waktu"), use_container_width=True)

    # Basic info
    info = suppliers.set_index('supplier_id').loc[sel].to_dict()
    st.json(info)
