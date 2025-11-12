
import streamlit as st, pandas as pd

def tweak_weights(gw: pd.Series, sub_ids: list, factor: float):
    if gw is None or gw.size==0: return gw
    w = gw.copy().astype(float)
    if sub_ids:
        w.loc[sub_ids] = w.loc[sub_ids] * float(factor)
    w = w / (w.sum() if w.sum()!=0 else 1.0)
    return w

def compare_rankings(ranking_base: pd.DataFrame, ranking_new: pd.DataFrame):
    if ranking_base is None or ranking_new is None or len(ranking_base)==0 or len(ranking_new)==0:
        st.info("Ranking tidak tersedia untuk komparasi.")
        return
    m = ranking_base[['supplier_id','score']].merge(ranking_new[['supplier_id','score']], on='supplier_id', suffixes=('_base','_new'))
    m['delta'] = m['score_new'] - m['score_base']
    st.dataframe(m.sort_values('delta', ascending=False))
