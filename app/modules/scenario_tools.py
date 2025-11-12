
import json
from pathlib import Path
import pandas as pd
from .what_if import tweak_weights
from .allocation_enhanced import optimize_allocation_enhanced
from .processing import supplier_scores

def capture_state(danp_gw, filters, optimizer_args, alloc_args):
    return {
        "filters": filters,
        "what_if": {"subs": [], "factor": 1.0},
        "optimizer": optimizer_args,
        "allocation": alloc_args,
        "gw_base": (danp_gw.to_dict() if danp_gw is not None else {})
    }

def _compute_kpis(alloc_df: pd.DataFrame, suppliers_df: pd.DataFrame, ranking_df: pd.DataFrame):
    if alloc_df is None or len(alloc_df)==0:
        return {"total_cost": 0.0, "avg_quality": 0.0, "total_emission": 0.0}
    s = suppliers_df.set_index('supplier_id')
    a = alloc_df.merge(s[['unit_cost','emission_score']].fillna(0), left_on='supplier_id', right_index=True, how='left')
    total_cost = float((a['quantity'] * a['unit_cost']).sum())
    total_emission = float((a['quantity'] * a['emission_score']).sum())
    if ranking_df is None or len(ranking_df)==0 or 'score' not in ranking_df.columns:
        avg_quality = 0.0
    else:
        max_score = max(1.0, float(ranking_df['score'].max()))
        qn = (ranking_df.set_index('supplier_id')['score'] / max_score).rename('Qn')
        a = a.join(qn, on='supplier_id')
        denom = float(a['quantity'].sum()) or 1.0
        avg_quality = float((a['Qn'] * a['quantity']).sum() / denom)
    return {"total_cost": total_cost, "avg_quality": avg_quality, "total_emission": total_emission}

def simulate_ranking_alloc(state, ratings, respondents, suppliers, plants_df, suppliers_df):
    gw_base = pd.Series(state.get("gw_base", {}), dtype=float)
    subs = state.get("what_if", {}).get("subs", [])
    factor = float(state.get("what_if", {}).get("factor", 1.0))
    gw_new = tweak_weights(gw_base, subs, factor) if gw_base.size>0 else gw_base
    ranking, _ = supplier_scores(ratings, respondents, gw_new, suppliers, filters=state.get("filters", {}))
    a = state.get("allocation", {})
    defaults = dict(qwt=1.0, cwt=0.2, rwt=0.5, preferred_regions=[], max_share_supplier=1.0, max_share_per_plant_supplier=1.0,
                    min_total_supplier=0.0, excluded_suppliers=[], min_quality_norm=0.0, region_min_shares={}, region_max_shares={},
                    ewt=0.0, max_total_emission=None)
    for k,v in defaults.items(): a.setdefault(k, v)
    alloc = optimize_allocation_enhanced(plants_df, suppliers_df, ranking, **a) if ranking is not None and len(ranking)>0 else None
    kpis = _compute_kpis(alloc, suppliers_df, ranking)
    return gw_new, ranking, alloc, kpis

def save_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f: json.dump(payload, f, indent=2)
