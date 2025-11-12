import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
from pathlib import Path
import traceback

# Import modules dengan error handling
try:
    from modules.themes import inject as inject_theme
    from modules.components import hero, kpi
    from modules.viz import heatmap, barh, bars, cause_effect_scatter, radar_weights, sankey_criteria
    from modules.supplier_profile import supplier_profile_view
    from modules.what_if import tweak_weights, compare_rankings
    from modules.scenarios import save_scenario, list_scenarios, load_scenario, delete_scenario
    from modules.processing import hor_stage1, hor_stage2, build_dematel, danp_from_T, supplier_scores
    from modules.optimizer import weighted_sum_selection, epsilon_constraint_TE
    from modules.allocation import optimize_allocation
    from modules.data_wizard import wizard as data_wizard
    from modules.mapper import map_columns_ui
    from modules.allocation_enhanced import optimize_allocation_enhanced
    from modules.pdf_story import build_story
    from modules.insights import auto_insights
    from modules.preflight import ensure_minimal_templates, preflight_report
    from modules.validator import validate_all
    from modules.data_fix import fix_all
    from modules.dummy_data import generate as gen_dummy
    
    # Smart mapper (optional)
    try:
        from modules.mapper_smart import smart_map_columns_ui
    except Exception as e:
        smart_map_columns_ui = None
        print(f"Smart mapper unavailable: {e}")
        
except ImportError as e:
    st.error(f"⚠️ Module import error: {e}")
    st.info("Pastikan semua file modules ada di folder yang benar")
    st.stop()

# ============================================================================
# CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Executive Dashboard – HOR + DEMATEL + DANP",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE = Path(__file__).resolve().parents[1]
TPL = BASE / 'data' / 'templates'
OUT = BASE / 'data' / 'output'
OUT.mkdir(parents=True, exist_ok=True)
TPL.mkdir(parents=True, exist_ok=True)

# ============================================================================
# HELPER FUNCTIONS - INDONESIAN COLUMN ALIASES
# ============================================================================
def _rename_if_present(df, mapping):
    """Rename columns safely without errors"""
    if df is None or not isinstance(df, pd.DataFrame):
        return df
    ren = {src: dst for src, dst in mapping.items() if src in df.columns}
    return df.rename(columns=ren) if ren else df


def _normalize_all_to_english(events, agents, actions, respondents,
                              criteria, subcriteria, edges,
                              suppliers, ratings):
    """Normalize Indonesian column names to English"""
    # Events
    events = _rename_if_present(events, {
        'id_kejadian': 'event_id',
        'nama_kejadian': 'event_name',
        'tingkat_keparahan': 'severity'
    })
    
    # Agents
    agents = _rename_if_present(agents, {
        'id_agen': 'agent_id',
        'nama_agen': 'agent_name',
        'frekuensi': 'occurrence'
    })
    
    # Actions
    actions = _rename_if_present(actions, {
        'id_aksi': 'action_id',
        'nama_aksi': 'action_name',
        'biaya': 'cost',
        'jam_kerja': 'manhours',
        'tingkat_kesulitan': 'difficulty',
        'gunakan_manual': 'use_manual'
    })
    
    # Respondents
    respondents = _rename_if_present(respondents, {
        'id_responden': 'respondent_id',
        'nama_responden': 'respondent_name',
        'bobot': 'weight'
    })
    
    # Criteria & Subcriteria
    criteria = _rename_if_present(criteria, {
        'id_kriteria': 'criterion_id',
        'nama_kriteria': 'criterion_name'
    })
    
    subcriteria = _rename_if_present(subcriteria, {
        'id_subkriteria': 'sub_id',
        'nama_subkriteria': 'sub_name',
        'id_kriteria': 'criterion_id'
    })
    
    # DEMATEL edges
    edges = _rename_if_present(edges, {
        'id_responden': 'respondent_id',
        'dari_sub': 'from_sub',
        'ke_sub': 'to_sub',
        'skor': 'score',
        'pengaruh': 'influence'
    })
    
    # Suppliers
    suppliers = _rename_if_present(suppliers, {
        'id_pemasok': 'supplier_id',
        'nama_pemasok': 'supplier_name',
        'wilayah': 'region'
    })
    
    # Ratings
    ratings = _rename_if_present(ratings, {
        'id_pemasok': 'supplier_id',
        'id_subkriteria': 'sub_id',
        'penilaian': 'rating',
        'id_responden': 'respondent_id',
        'jenis_keju': 'cheese_type',
        'id_pabrik': 'plant_id',
        'periode_waktu': 'time_period'
    })
    
    return (events, agents, actions, respondents,
            criteria, subcriteria, edges, suppliers, ratings)


def _norm_ids(x):
    # seragamkan ID: string, trim spasi, hilangkan BOM, huruf besar-kecil disamakan
    return (x.astype(str)
              .str.replace('\ufeff', '', regex=False)
              .str.strip())

def align_effectiveness(E, actions, agents, *, fill=0.0):
    """Selaraskan E (rows=action_id, cols=agent_id) ke master.
       Auto-detect transpose, buang ID nyasar, isi yang hilang."""
    if E is None or E.empty or actions is None or actions.empty or agents is None or agents.empty:
        return pd.DataFrame()

    # master ids
    if 'action_id' in actions.columns:
        act_ids = _norm_ids(actions['action_id'])
    else:
        act_ids = _norm_ids(actions.index.to_series())
    agt_ids = _norm_ids(agents['agent_id'])

    # normalisasi E
    E = E.copy()
    # kalau masih ada kolom 'action_id' di E (format long/terekspor Excel)
    if 'action_id' in E.columns:
        E = E.set_index('action_id')
    E.index   = _norm_ids(E.index.to_series())
    E.columns = _norm_ids(pd.Index(E.columns))

    # --- Heuristik orientasi (apakah E kebalik?) ---
    hits_row_act = len(set(E.index)   & set(act_ids))
    hits_col_ag  = len(set(E.columns) & set(agt_ids))
    hits_row_ag  = len(set(E.index)   & set(agt_ids))
    hits_col_act = len(set(E.columns) & set(act_ids))
    if hits_row_ag > hits_row_act and hits_col_act > hits_col_ag:
        # kemungkinan besar E = agents x actions -> balikkan
        E = E.T
        # normalisasi ulang kolom/index pasca-transpose
        E.index   = _norm_ids(E.index.to_series())
        E.columns = _norm_ids(pd.Index(E.columns))

    # --- Hitung mismatch SEBELUM perbaikan (sekadar info) ---
    before_miss_rows  = sorted(set(act_ids) - set(E.index))
    before_miss_cols  = sorted(set(agt_ids) - set(E.columns))
    before_extra_rows = sorted(set(E.index)   - set(act_ids))
    before_extra_cols = sorted(set(E.columns) - set(agt_ids))

    # Tambah baris/kolom yang hilang
    if before_miss_rows:
        E = pd.concat([E, pd.DataFrame(fill, index=before_miss_rows, columns=E.columns)], axis=0)
    for c in before_miss_cols:
        if c not in E.columns:
            E[c] = fill

    # Buang yang tidak dikenal & reindex ke urutan master
    E = E.loc[act_ids.unique(), [c for c in agt_ids.unique() if c in E.columns]]

    # Pastikan numerik
    E = E.apply(pd.to_numeric, errors='coerce').fillna(fill)

    # --- Cek mismatch SESUDAH perbaikan; warning hanya kalau masih ada ---
    after_miss_rows = sorted(set(act_ids) - set(E.index))
    after_miss_cols = sorted(set(agt_ids) - set(E.columns))
    if after_miss_rows or after_miss_cols:
        st.warning(
            f"E masih tidak selaras setelah perbaikan. "
            f"Missing actions(row): {len(after_miss_rows)}, missing agents(col): {len(after_miss_cols)}"
        )
        # Tampilkan contoh ID yang hilang (maks 5) agar mudah koreksi CSV
        if after_miss_rows:
            st.caption("Contoh action_id yang hilang: " + ", ".join(after_miss_rows[:5]))
        if after_miss_cols:
            st.caption("Contoh agent_id yang hilang: " + ", ".join(after_miss_cols[:5]))
    else:
        # Kalau ingin tahu kondisi awalnya, tampilkan sebagai info sekali
        if before_miss_rows or before_miss_cols or before_extra_rows or before_extra_cols:
            st.info(
                f"E awalnya tidak selaras "
                f"(missing rows {len(before_miss_rows)}, missing cols {len(before_miss_cols)}, "
                f"extra rows {len(before_extra_rows)}, extra cols {len(before_extra_cols)}) — "
                f"sudah diperbaiki otomatis."
            )

    return E

def align_R(R, events, agents, *, fill=0):
    """Selaraskan R (rows=event_id, cols=agent_id). Auto-transpose bila perlu."""
    if R is None or R.empty or events is None or events.empty or agents is None or agents.empty:
        return pd.DataFrame()

    ev_ids = _norm_ids(events['event_id'] if 'event_id' in events.columns else events.index.to_series())
    ag_ids = _norm_ids(agents['agent_id'])

    R = R.copy()
    R.index   = _norm_ids(R.index.to_series())
    R.columns = _norm_ids(pd.Index(R.columns))

    # Heuristik orientasi
    hit_row_ev = len(set(R.index)   & set(ev_ids))
    hit_col_ag = len(set(R.columns) & set(ag_ids))
    hit_row_ag = len(set(R.index)   & set(ag_ids))
    hit_col_ev = len(set(R.columns) & set(ev_ids))
    if hit_row_ag > hit_row_ev and hit_col_ev > hit_col_ag:
        R = R.T
        R.index   = _norm_ids(R.index.to_series())
        R.columns = _norm_ids(pd.Index(R.columns))

    # Reindex aman
    R = R.reindex(index=ev_ids.unique()).reindex(columns=ag_ids.unique()).fillna(fill)
    R = R.apply(pd.to_numeric, errors='coerce').fillna(fill)
    return R

# ============================================================================
# DATA LOADING
# ============================================================================
@st.cache_data(ttl=300)
def _load_all():
    """Load all CSV files with error handling and caching"""
    try:
        # Ensure minimal templates exist
        ensure_minimal_templates(TPL)
        
        # Load CSV files
        events = pd.read_csv(TPL / 'hor_events.csv')
        agents = pd.read_csv(TPL / 'hor_agents.csv')
        R = pd.read_csv(TPL / 'hor_R.csv', index_col=0)
        actions = pd.read_csv(TPL / 'hor_actions.csv')
        E = pd.read_csv(TPL/'hor_effectiveness.csv', index_col=0)
        respondents = pd.read_csv(TPL / 'respondents.csv')
        criteria = pd.read_csv(TPL / 'criteria.csv')
        subcriteria = pd.read_csv(TPL / 'subcriteria.csv')
        edges = pd.read_csv(TPL / 'dematel_edges.csv')
        suppliers = pd.read_csv(TPL / 'suppliers.csv')
        ratings = pd.read_csv(TPL / 'supplier_ratings.csv')
        
        # Normalize column names
        (events, agents, actions, respondents,
         criteria, subcriteria, edges, suppliers, ratings) = _normalize_all_to_english(
            events, agents, actions, respondents, criteria, subcriteria, edges, suppliers, ratings
        )
        
        # Set index for actions safely
        if 'action_id' in actions.columns:
            actions = actions.set_index('action_id')

        else:
            st.warning("⚠️ 'action_id' column not found in hor_actions.csv")

        R = align_R(R, events, agents, fill=0)
        E = align_effectiveness(E, actions, agents, fill=0.0)
        return events, agents, R, actions, E, respondents, criteria, subcriteria, edges, suppliers, ratings
        
    except Exception as e:
        st.error(f"❌ Failed to load templates: {e}")
        st.info("💡 Tip: Upload CSV files via Data Wizard or generate dummy data")
        
        # Return empty dataframes as fallback
        return (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
                pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
                pd.DataFrame(), pd.DataFrame(), pd.DataFrame())


# ============================================================================
# THEME SETUP
# ============================================================================
theme = st.sidebar.selectbox("🎨 Theme", ["Ocean", "Sunset", "Emerald", "Mono"], index=0)

# Set plotly template for better chart contrast
PLOTLY_TPL = {
    "Ocean": "plotly_white",
    "Sunset": "plotly",
    "Emerald": "ggplot2",
    "Mono": "plotly_white",
}
pio.templates.default = PLOTLY_TPL.get(theme, "plotly_white")

inject_theme(theme)

# ============================================================================
# HEADER
# ============================================================================
hero(
    "All-in-one Risk & Supplier Analytics",
    "HOR → DEMATEL → DANP → Suppliers → Optimizer → Allocation → Export PDF/Excel"
)

# ============================================================================
# LOAD DATA
# ============================================================================
(events, agents, R, actions, E, respondents,
 criteria, subcriteria, edges, suppliers, ratings) = _load_all()

# Sanity checks (opsional tapi membantu)
# R: index = event_id, columns = agent_id
if 'event_id' in events.columns:
    expect_events = events['event_id'].astype(str)
else:
    expect_events = events.index.astype(str)

if 'agent_id' in agents.columns:
    expect_agents = agents['agent_id'].astype(str)
else:
    expect_agents = agents.index.astype(str)

# Selaraskan R
R.index   = R.index.astype(str)
R.columns = R.columns.astype(str)
missing_e = set(expect_events) - set(R.index)
missing_a = set(expect_agents) - set(R.columns)
if missing_e or missing_a:
    st.warning(f"R tidak selaras. Missing events: {len(missing_e)}, missing agents: {len(missing_a)}")

# E: rows = action_id, columns = agent_id
if 'action_id' in actions.columns:
    expect_actions = actions['action_id'].astype(str)
else:
    expect_actions = actions.index.astype(str)

# ============================================================================
# TABS
# ============================================================================
tabs = st.tabs([
    "🏠 Home",
    "🧙 Data Wizard",
    "📊 HOR",
    "🛡️ Mitigation",
    "🔗 DEMATEL",
    "⚖️ DANP",
    "🏢 Suppliers",
    "👤 Supplier Profile",
    "🧪 Labs",
    "🎯 Optimizer",
    "📤 Export"
])

home, wizard, tab1, tab2, tab3, tab4, tab5, profile, labs, tab6, tab7 = tabs

# ============================================================================
# HOME TAB
# ============================================================================
with home:
    st.subheader("📋 Preflight Report")
    
    try:
        _pf = preflight_report(TPL)
        _pf['icon'] = _pf['status'].map({'OK': '✅', 'MISSING': '❌'}).fillna('❌')
        st.dataframe(_pf[['icon', 'file', 'status', 'rows', 'cols']], use_container_width=True)
    except Exception as e:
        st.warning(f"Preflight check skipped: {e}")
    
    # Quick KPIs
    try:
        weighted, ARP = hor_stage1(events, agents, R)
        detail = hor_stage2(E, ARP, actions)
        
        col = st.columns(3)
        if detail is not None and not detail.empty:
            col[0].metric("Total TE", f"{detail['TE'].sum():.1f}")
            col[1].metric("Top ETD", f"{detail['ETD'].max():.2f}")
        else:
            col[0].metric("Total TE", "N/A")
            col[1].metric("Top ETD", "N/A")
        
        col[2].metric("Risk Agents", f"{len(ARP) if ARP is not None else 0}")
        
        # Chart
        if ARP is not None and len(ARP) > 0:
            st.plotly_chart(
                bars(ARP.index, ARP.values, "ARP per Agent", "Agent", "ARP"),
                use_container_width=True
            )
    except Exception as e:
        st.error(f"Error computing KPIs: {e}")

# ============================================================================
# DATA WIZARD TAB
# ============================================================================
with wizard:
    data_wizard(TPL, OUT)
    
    st.markdown('---')
    colx = st.columns(3)
    
    if colx[0].button('✨ Generate Dummy Data'):
        try:
            stats = gen_dummy(TPL)
            st.success(f"✅ Dummy data generated: {stats}")
            st.cache_data.clear()  # Clear cache to reload data
        except Exception as e:
            st.error(f"Error generating dummy data: {e}")
    
    if colx[1].button('🧼 Auto Fix Common Issues'):
        try:
            log = fix_all(TPL, OUT)
            st.dataframe(log, use_container_width=True)
            log.to_csv(OUT / 'autofix_log.csv', index=False)
            st.success('✅ Autofix log saved to output folder')
            st.cache_data.clear()
        except Exception as e:
            st.error(f"Error in auto fix: {e}")
    
    st.markdown('---')
    
    # Basic mapper
    try:
        map_columns_ui(TPL)
    except Exception as e:
        st.error(f"Column mapper error: {e}")
    
    # Smart mapper
    if smart_map_columns_ui:
        try:
            smart_map_columns_ui(TPL, key_prefix="smart_mapper_v14")
        except Exception as e:
            st.error(f"Smart mapper error: {e}")
    else:
        st.info("ℹ️ Smart Column Mapper not available. Use basic mapper above.")
    
    st.markdown('---')
    st.subheader('🔍 Validation')
    
    if st.button('Run Validation'):
        try:
            rep = validate_all(TPL)
            st.dataframe(rep, use_container_width=True)
            rep.to_csv(OUT / 'validation_report.csv', index=False)
            st.success('✅ Validation report saved')
        except Exception as e:
            st.error(f"Validation error: {e}")

# ============================================================================
# HOR STAGE 1 TAB
# ============================================================================
with tab1:
    st.subheader("📊 HOR – Stage 1")
    
    try:
        weighted, ARP = hor_stage1(events, agents, R)
        
        if weighted is not None and not weighted.empty:
            st.plotly_chart(
                heatmap(weighted, "Weighted S×R (Events × Agents)"),
                use_container_width=True
            )
        else:
            st.info('ℹ️ No data for HOR Stage 1')
        
        if ARP is not None and len(ARP) > 0:
            st.plotly_chart(
                bars(ARP.index, ARP.values, "ARP per Agent", "Agent", "ARP"),
                use_container_width=True
            )
        else:
            st.info('ℹ️ ARP is empty')
            
    except Exception as e:
        st.error(f"Error in HOR Stage 1: {e}")
        st.code(traceback.format_exc())

# ============================================================================
# HOR STAGE 2 TAB (MITIGATION)
# ============================================================================
with tab2:
    st.subheader("🛡️ HOR – Stage 2 (TE & ETD)")
    
    try:
        weighted, ARP = hor_stage1(events, agents, R)
        detail = hor_stage2(E, ARP, actions)
        dem = build_dematel(respondents, subcriteria, edges)
        danp = danp_from_T(subcriteria, criteria, dem.get('T', pd.DataFrame()))
        
        if detail is not None and not detail.empty:
            st.plotly_chart(
                barh(detail['ETD'].head(15), "Top Actions by ETD", "ETD"),
                use_container_width=True
            )
            st.dataframe(detail, use_container_width=True)
        else:
            st.info('ℹ️ No ETD data available')
            
    except Exception as e:
        st.error(f"Error in HOR Stage 2: {e}")

# ============================================================================
# DEMATEL TAB
# ============================================================================
with tab3:
    st.subheader("🔗 DEMATEL")
    
    try:
        dem = build_dematel(respondents, subcriteria, edges)
        
        if dem and 'alpha' in dem:
            st.caption(f"α = {dem.get('alpha', 1.0):.6f}")
        
        if dem and dem.get('T') is not None and not dem['T'].empty:
            st.plotly_chart(
                heatmap(dem['T'], "Total Relation Matrix T"),
                use_container_width=True
            )
            
            rc = pd.DataFrame({
                'r': dem['r'],
                'c': dem['c'],
                'prominence': dem['r'] + dem['c'],
                'relation': dem['r'] - dem['c']
            }).sort_values('prominence', ascending=False)
            
            st.dataframe(rc, use_container_width=True)
            
            st.plotly_chart(
                cause_effect_scatter(dem['r'], dem['c']),
                use_container_width=True
            )
        else:
            st.info('ℹ️ DEMATEL matrix T is empty')
            
    except Exception as e:
        st.error(f"Error in DEMATEL: {e}")
        st.code(traceback.format_exc())

# ============================================================================
# DANP TAB
# ============================================================================
with tab4:
    st.subheader("⚖️ DANP")
    
    try:
        dem = build_dematel(respondents, subcriteria, edges)
        danp = danp_from_T(subcriteria, criteria, dem.get('T'))
        
        if danp and danp.get('gw') is not None and len(danp['gw']) > 0:
            st.plotly_chart(
                barh(danp['gw'].sort_values(ascending=False).head(20),
                     "Global Weights (Top 20)", "Weight"),
                use_container_width=True
            )
            
            st.dataframe(
                danp['gw'].rename('global_weight').to_frame(),
                use_container_width=True
            )
            
            st.plotly_chart(
                radar_weights(danp['gw'], "Radar – Top Weights"),
                use_container_width=True
            )
        else:
            st.info('ℹ️ DANP global weights not available')
        
        if danp and danp.get('Td') is not None and not danp['Td'].empty:
            st.plotly_chart(
                sankey_criteria(danp['Td']),
                use_container_width=True
            )
        else:
            st.info('ℹ️ Sankey diagram skipped (T_d empty)')
            
    except Exception as e:
        st.error(f"Error in DANP: {e}")
        st.code(traceback.format_exc())

# ============================================================================
# SUPPLIERS TAB
# ============================================================================
with tab5:
    st.subheader("🏢 Suppliers – Filter & KPI")
    
    try:
        # Filters
        cols = st.columns(3)
        
        types = ['ALL']
        if 'cheese_type' in ratings.columns:
            types += sorted(ratings['cheese_type'].dropna().unique().tolist())
        
        plants = ['ALL']
        if 'plant_id' in ratings.columns:
            plants += sorted(ratings['plant_id'].dropna().unique().tolist())
        
        periods = ['ALL']
        if 'time_period' in ratings.columns:
            periods += sorted(ratings['time_period'].dropna().unique().tolist())
        
        f_type = cols[0].selectbox("Cheese Type", types, index=0)
        f_plant = cols[1].selectbox("Plant", plants, index=0)
        f_period = cols[2].selectbox("Period", periods, index=0)
        
        filters = {
            'cheese_type': f_type,
            'plant_id': f_plant,
            'time_period': f_period
        }
        
        # Compute scores
        dem = build_dematel(respondents, subcriteria, edges)
        danp = danp_from_T(subcriteria, criteria, dem.get('T'))
        
        ranking, agg = supplier_scores(
            ratings, respondents, danp.get('gw'), suppliers, filters=filters
        )
        
        # Display KPIs
        c1, c2, c3 = st.columns(3)
        
        if ranking is not None and len(ranking) > 0:
            top = ranking.iloc[0]
            c1.metric("Top Supplier", top['supplier_id'])
            c2.metric("Top Score", f"{top['score']:.3f}")
            c3.metric("Suppliers Count", len(ranking))
            
            st.plotly_chart(
                barh(ranking.set_index('supplier_id')['score'].head(12),
                     "Top Suppliers (Filtered)", "Score"),
                use_container_width=True
            )
            
            st.dataframe(ranking, use_container_width=True)
        else:
            st.info('ℹ️ No supplier rankings for current filters')
            
    except Exception as e:
        st.error(f"Error in Suppliers: {e}")
        st.code(traceback.format_exc())

# ============================================================================
# SUPPLIER PROFILE TAB
# ============================================================================
with profile:
    st.subheader("👤 Supplier Profile")
    
    try:
        # Recompute unfiltered rankings
        dem = build_dematel(respondents, subcriteria, edges)
        danp = danp_from_T(subcriteria, criteria, dem.get('T'))
        ranking_all, agg_all = supplier_scores(
            ratings, respondents, danp.get('gw'), suppliers
        )
        
        supplier_profile_view(
            ranking_all, agg_all, danp.get('gw'),
            suppliers, ratings, subcriteria, criteria
        )
        
    except Exception as e:
        st.error(f"Error in Supplier Profile: {e}")

# ============================================================================
# LABS TAB (WHAT-IF & SCENARIOS)
# ============================================================================
with labs:
    st.subheader("🧪 Labs – What-If & Scenarios")
    
    try:
        # Get global weights
        dem = build_dematel(respondents, subcriteria, edges)
        danp = danp_from_T(subcriteria, criteria, dem.get('T'))
        gw_series = danp.get('gw') if danp else None
        
        subs = gw_series.index.tolist() if gw_series is not None and len(gw_series) > 0 else []
        
        sel_subs = st.multiselect("Select Subcriteria to Adjust", subs)
        factor = st.slider("Adjustment Factor", 0.5, 2.0, 1.2, 0.05)
        
        # Base ranking
        ranking_base, _ = supplier_scores(ratings, respondents, gw_series, suppliers)
        
        # What-if ranking
        if len(sel_subs) > 0:
            gw_new = tweak_weights(gw_series, sel_subs, factor)
            ranking_new, _ = supplier_scores(ratings, respondents, gw_new, suppliers)
            
            st.markdown("**📊 Delta Ranking (new − base)**")
            compare_rankings(ranking_base, ranking_new)
        
        st.markdown('---')
        st.markdown("**💾 Scenarios** – Save & load What-If configurations")
        
        scn_name = st.text_input("Scenario Name", "scenario_1")
        
        if st.button("💾 Save Scenario"):
            try:
                payload = {
                    "what_if": {
                        "subs": sel_subs,
                        "factor": float(factor)
                    }
                }
                path = save_scenario(OUT, scn_name, payload)
                st.success(f"✅ Saved: {path}")
            except Exception as e:
                st.error(f"Failed to save scenario: {e}")
                
    except Exception as e:
        st.error(f"Error in Labs: {e}")
        st.code(traceback.format_exc())

# ============================================================================
# OPTIMIZER & ALLOCATION TAB
# ============================================================================
with tab6:
    st.subheader("🎯 Optimizer – Mitigation Actions")
    
    try:
        # Get action details
        weighted, ARP = hor_stage1(events, agents, R)
        detail = hor_stage2(E, ARP, actions)
        
        if detail is None or detail.empty:
            st.info("ℹ️ No actions available for optimization")
        else:
            # Optimizer parameters
            budget_cost = st.number_input(
                "Budget Cost",
                min_value=0,
                value=int(detail['Cost'].sum() * 0.6)
            )
            
            budget_mh = st.number_input(
                "Budget Manhours",
                min_value=0,
                value=int(detail.get('manhours', 0).sum() * 0.6)
            )
            
            w_cost = st.slider("Penalty – Cost", 0.0, 1.0, 0.1)
            w_mh = st.slider("Penalty – Manhours", 0.0, 1.0, 0.1)
            
            # Run optimizer
            sel, totals = weighted_sum_selection(
                detail, budget_cost, budget_mh,
                w_te=1.0, w_cost=w_cost, w_mh=w_mh
            )
            
            if sel is not None and not sel.empty:
                st.success(
                    f"✅ Selected {len(sel)} actions • "
                    f"TE={totals.get('TE', 0):.1f} • "
                    f"Cost={totals.get('Cost', 0):.1f} • "
                    f"MH={totals.get('Manhours', 0):.1f}"
                )
                st.dataframe(sel, use_container_width=True)
            else:
                st.info("ℹ️ No actions selected (check constraints)")
            
            # Pareto frontier
            st.markdown("**📈 Pareto Frontier (epsilon-constraint)**")
            
            targets = np.linspace(
                detail['TE'].sum() * 0.2,
                min(detail['TE'].sum(), detail['TE'].sum() * 0.95),
                10
            )
            
            frontier = epsilon_constraint_TE(detail, budget_cost, budget_mh, targets)
            
            if not frontier.empty:
                st.plotly_chart(
                    px.scatter(frontier, x='Cost', y='TE', title='Pareto TE vs Cost'),
                    use_container_width=True
                )
                st.dataframe(frontier, use_container_width=True)
            else:
                st.info("ℹ️ No frontier solutions found")
    
    except Exception as e:
        st.error(f"Error in Optimizer: {e}")
        st.code(traceback.format_exc())
    
    st.markdown('---')
    st.subheader("🏭 Allocation – Multi-Plant (Advanced)")
    
    try:
        # Load/create allocation data
        alloc_plants = TPL / "allocation_plants.csv"
        alloc_suppliers = TPL / "allocation_suppliers.csv"
        
        # Plants
        if alloc_plants.exists():
            plants_df = pd.read_csv(alloc_plants)
        else:
            plants_df = pd.DataFrame({
                "plant_id": ["PlantA", "PlantB"],
                "demand": [100, 120]
            })
            plants_df.to_csv(alloc_plants, index=False)
        
        # Suppliers
        if alloc_suppliers.exists():
            suppliers_df = pd.read_csv(alloc_suppliers)
        else:
            n = min(4, len(suppliers)) if not suppliers.empty else 1
            if n == 0:
                ids = ["S1"]
                capacity = [100]
                unit_cost = [4.2]
                emission = [0.8]
            else:
                ids = suppliers["supplier_id"].head(n).astype(str).tolist()
                capacity = [150, 120, 90, 80][:n]
                unit_cost = [4.5, 4.2, 4.0, 4.1][:n]
                emission = [0.6, 0.8, 1.0, 0.7][:n]
            
            suppliers_df = pd.DataFrame({
                "supplier_id": ids,
                "capacity": capacity,
                "unit_cost": unit_cost,
                "emission_score": emission,
            })
            suppliers_df.to_csv(alloc_suppliers, index=False)
        
        # Ensure required columns
        for col, default in [("capacity", 0), ("unit_cost", 0.0), ("emission_score", 0.0)]:
            if col not in suppliers_df.columns:
                suppliers_df[col] = default
        
        st.dataframe(plants_df, use_container_width=True)
        st.dataframe(suppliers_df, use_container_width=True)
        
        # Allocation parameters
        qwt = st.slider("Quality weight", 0.0, 2.0, 1.0, 0.05)
        cwt = st.slider("Cost penalty", 0.0, 1.0, 0.2, 0.05)
        rwt = st.slider("Region bonus weight", 0.0, 2.0, 0.5, 0.05)
        ewt = st.slider("Emission penalty weight", 0.0, 2.0, 0.0, 0.05)
        
        max_emis = st.number_input("Max total emission (optional)", min_value=0.0, value=0.0, step=10.0)
        max_emis = None if max_emis == 0 else max_emis
        
        pref_regions = st.multiselect(
            "Preferred regions",
            sorted(suppliers['region'].dropna().unique().tolist())
        )
        
        max_share_sup = st.slider(
            "Max share per supplier (% of total demand)",
            0, 100, 100, 5
        ) / 100.0
        
        max_share_pps = st.slider(
            "Max share per supplier per plant (% of plant demand)",
            0, 100, 100, 5
        ) / 100.0
        
        min_total_supp = st.number_input(
            "Min total per supplier (absolute units)",
            min_value=0.0, value=0.0, step=10.0
        )
        
        excluded = st.multiselect(
            "Exclude suppliers",
            sorted(suppliers['supplier_id'].dropna().unique().tolist())
        )
        
        qfloor = st.slider("Minimum quality (normalized Qn)", 0.0, 1.0, 0.0, 0.05)
        
        with st.expander("🌍 Region min/max share constraints (%)"):
            regions = sorted(suppliers['region'].dropna().unique().tolist())
            if len(regions) > 0:
                dfc = pd.DataFrame({
                    'region': regions,
                    'min_pct': [0] * len(regions),
                    'max_pct': [100] * len(regions)
                })
                dfc = st.data_editor(dfc, num_rows='fixed', use_container_width=True)
            else:
                dfc = pd.DataFrame(columns=['region', 'min_pct', 'max_pct'])
        
        # Run allocation
        dem = build_dematel(respondents, subcriteria, edges)
        danp = danp_from_T(subcriteria, criteria, dem.get('T'))
        ranking_all, _ = supplier_scores(ratings, respondents, danp.get('gw'), suppliers)
        
        if ranking_all is None or len(ranking_all) == 0:
            st.info('ℹ️ Allocation skipped: no supplier rankings available')
        else:
            rmins = {r: float(m) / 100.0 for r, m in zip(dfc['region'], dfc['min_pct']) if m and m > 0}
            rmaxs = {r: float(m) / 100.0 for r, m in zip(dfc['region'], dfc['max_pct']) if m and m < 100}
            
            sol = optimize_allocation_enhanced(
                plants_df, suppliers_df, ranking_all,
                qwt=qwt, cwt=cwt, rwt=rwt, preferred_regions=pref_regions,
                max_share_supplier=max_share_sup,
                max_share_per_plant_supplier=max_share_pps,
                min_total_supplier=min_total_supp,
                excluded_suppliers=excluded, min_quality_norm=qfloor,
                region_min_shares=rmins, region_max_shares=rmaxs,
                ewt=ewt, max_total_emission=max_emis,
            )
            
            if sol is None or sol.empty:
                st.info('ℹ️ No allocation found (check demand/capacity & constraints)')
            else:
                st.success(f"✅ Allocated {len(sol)} assignments")
                st.dataframe(sol, use_container_width=True)
                
                # Calculate KPIs
                try:
                    sidx = suppliers_df.set_index('supplier_id')
                    merged = sol.merge(
                        sidx[['unit_cost', 'emission_score']].fillna(0),
                        left_on='supplier_id',
                        right_index=True,
                        how='left'
                    )
                    
                    total_cost = float((merged['quantity'] * merged['unit_cost']).sum())
                    total_emis = float((merged['quantity'] * merged['emission_score']).sum())
                    
                    max_score = max(1.0, float(ranking_all['score'].max()))
                    qn = (ranking_all.set_index('supplier_id')['score'] / max_score).rename('Qn')
                    merged = merged.join(qn, on='supplier_id')
                    
                    avg_q = float((merged['Qn'] * merged['quantity']).sum() / (merged['quantity'].sum() or 1.0))
                    
                    k1, k2, k3 = st.columns(3)
                    k1.metric('💰 Total Cost', f"{total_cost:,.2f}")
                    k2.metric('⭐ Avg Quality (Qn)', f"{avg_q:.3f}")
                    k3.metric('🌍 Total Emission', f"{total_emis:,.2f}")
                    
                except Exception as e:
                    st.info(f'ℹ️ KPI calculation skipped: {e}')
    
    except Exception as e:
        st.error(f"Error in Allocation: {e}")
        st.code(traceback.format_exc())

# ============================================================================
# EXPORT TAB
# ============================================================================
with tab7:
    st.subheader("📤 Export")
    
    # Logo upload
    logo_file = st.file_uploader(
        'Upload logo (PNG/JPG) for reports (optional)',
        type=['png', 'jpg', 'jpeg']
    )
    
    logo_path = None
    if logo_file is not None:
        logo_path = OUT / 'report_logo.png'
        with open(logo_path, 'wb') as f:
            f.write(logo_file.read())
        st.success("✅ Logo uploaded")
    
    # Excel Export
    st.markdown("### 📊 Excel Export")
    
    if st.button('📥 Generate Excel Report'):
        try:
            with pd.ExcelWriter(OUT / 'dashboard_exports.xlsx', engine='xlsxwriter') as w:
                # Recompute all data
                weighted, ARP = hor_stage1(events, agents, R)
                detail = hor_stage2(E, ARP, actions)
                dem = build_dematel(respondents, subcriteria, edges)
                danp = danp_from_T(subcriteria, criteria, dem.get('T'))
                ranking_all, _ = supplier_scores(ratings, respondents, danp.get('gw'), suppliers)
                
                # Write sheets
                if not weighted.empty:
                    weighted.to_excel(w, sheet_name='Weighted_SxR')
                
                if len(ARP) > 0:
                    ARP.rename('ARP').to_frame().to_excel(w, sheet_name='ARP')
                
                if not detail.empty:
                    detail.to_excel(w, sheet_name='ETD')
                
                if dem.get('A') is not None and not dem['A'].empty:
                    dem['A'].to_excel(w, sheet_name='DEMATEL_A')
                
                if dem.get('T') is not None and not dem['T'].empty:
                    dem['T'].to_excel(w, sheet_name='DEMATEL_T')
                
                if danp.get('gw') is not None and len(danp['gw']) > 0:
                    danp['gw'].rename('weight').to_frame().to_excel(w, sheet_name='DANP_weights')
                
                if ranking_all is not None and not ranking_all.empty:
                    ranking_all.to_excel(w, sheet_name='Supplier_Ranking', index=False)
            
            st.success("✅ Excel file created: dashboard_exports.xlsx")
            
            # Download button
            with open(OUT / 'dashboard_exports.xlsx', 'rb') as f:
                st.download_button(
                    label="⬇️ Download Excel",
                    data=f,
                    file_name='dashboard_exports.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
        
        except Exception as e:
            st.error(f"Error generating Excel: {e}")
            st.code(traceback.format_exc())
    
    st.markdown('---')
    st.markdown("### 📄 PDF Export")
    
    # Narrative PDF with KPIs
    if st.button('📝 Create Narrative PDF (with KPIs)'):
        try:
            # Recompute data
            weighted, ARP = hor_stage1(events, agents, R)
            detail = hor_stage2(E, ARP, actions)
            dem = build_dematel(respondents, subcriteria, edges)
            danp = danp_from_T(subcriteria, criteria, dem.get('T'))
            ranking_all, _ = supplier_scores(ratings, respondents, danp.get('gw'), suppliers)
            
            # Calculate KPIs
            kpis = {
                'Total TE': f"{detail['TE'].sum():.1f}" if detail is not None and not detail.empty else 'n/a',
                'Top ETD': f"{detail['ETD'].max():.2f}" if detail is not None and not detail.empty else 'n/a',
                'Top Supplier': (ranking_all.iloc[0]['supplier_id'] if ranking_all is not None and len(ranking_all) > 0 else 'n/a')
            }
            
            # Generate insights
            try:
                sol_var = None  # Will be set if allocation was run
                paragraphs = auto_insights(weighted, ARP, detail, dem, danp, ranking_all, sol_var)
            except:
                paragraphs = []
            
            if not paragraphs:
                paragraphs = [
                    '📊 Summary not available due to limited data.',
                    '💡 Upload data via Data Wizard to generate insights.'
                ]
            
            # Build PDF
            story_path = OUT / 'dashboard_story.pdf'
            build_story(story_path, 'Executive Narrative Report', kpis, paragraphs, logo_path=logo_path)
            
            st.success('✅ Narrative PDF created: dashboard_story.pdf')
            
            # Download button
            with open(story_path, 'rb') as f:
                st.download_button(
                    label="⬇️ Download Narrative PDF",
                    data=f,
                    file_name='dashboard_story.pdf',
                    mime='application/pdf'
                )
        
        except Exception as e:
            st.error(f"Error creating narrative PDF: {e}")
            st.code(traceback.format_exc())
    
    st.markdown('---')
    
    # Charts to PDF
    if st.button('📊 Create Charts PDF Report'):
        try:
            # Recompute all data
            weighted, ARP = hor_stage1(events, agents, R)
            detail = hor_stage2(E, ARP, actions)
            dem = build_dematel(respondents, subcriteria, edges)
            danp = danp_from_T(subcriteria, criteria, dem.get('T'))
            ranking_all, _ = supplier_scores(ratings, respondents, danp.get('gw'), suppliers)
            
            img_paths = {}
            
            # Generate chart images
            if weighted is not None and not weighted.empty:
                fig1 = heatmap(weighted, "Weighted S×R")
                p1 = OUT / 'fig_weighted.png'
                pio.write_image(fig1, p1, scale=2, width=1200, height=700)
                img_paths['HOR – Weighted S×R'] = p1
            
            if ARP is not None and len(ARP) > 0:
                fig2 = bars(ARP.index, ARP.values, "ARP per Agent", "Agent", "ARP")
                p2 = OUT / 'fig_arp.png'
                pio.write_image(fig2, p2, scale=2, width=1200, height=700)
                img_paths['HOR – ARP per Agent'] = p2
            
            if detail is not None and not detail.empty:
                fig3 = barh(detail['ETD'].head(15), "Top ETD", "ETD")
                p3 = OUT / 'fig_etd.png'
                pio.write_image(fig3, p3, scale=2, width=1200, height=700)
                img_paths['Mitigation – Top ETD'] = p3
            
            if dem.get('T') is not None and not dem['T'].empty:
                fig4 = heatmap(dem['T'], "DEMATEL – T")
                p4 = OUT / 'fig_T.png'
                pio.write_image(fig4, p4, scale=2, width=1200, height=700)
                img_paths['DEMATEL – Total Relation T'] = p4
            
            if danp.get('gw') is not None and len(danp['gw']) > 0:
                fig5 = barh(danp['gw'].sort_values(ascending=False).head(20),
                           "DANP – Global Weights", "Weight")
                p5 = OUT / 'fig_weights.png'
                pio.write_image(fig5, p5, scale=2, width=1200, height=700)
                img_paths['DANP – Global Weights'] = p5
            
            if len(img_paths) == 0:
                st.info('ℹ️ No charts available for PDF')
            else:
                # Build PDF with charts
                from modules.pdf_export_full import build_full_report
                pdf_path = OUT / 'dashboard_report.pdf'
                build_full_report(
                    pdf_path,
                    "Executive Dashboard Report",
                    images_map=img_paths,
                    notes="Auto-generated report with charts."
                )
                
                st.success("✅ Charts PDF created: dashboard_report.pdf")
                
                # Download button
                with open(pdf_path, 'rb') as f:
                    st.download_button(
                        label="⬇️ Download Charts PDF",
                        data=f,
                        file_name='dashboard_report.pdf',
                        mime='application/pdf'
                    )
        
        except Exception as e:
            st.warning(f"⚠️ PDF export failed (kaleido required): {e}")
            st.info("💡 Chart PNG files are saved in the output folder")
            st.code(traceback.format_exc())

# ============================================================================
# FOOTER
# ============================================================================
st.markdown('---')
st.caption('🚀 Executive Dashboard v2.0 | HOR + DEMATEL + DANP + Multi-objective Optimization')
st.caption('Made with ❤️ using Streamlit')