
import pandas as pd, numpy as np, pulp

def optimize_allocation_enhanced(plants_df: pd.DataFrame, suppliers_df: pd.DataFrame, ranking_df: pd.DataFrame,
                                 qwt=1.0, cwt=0.0, rwt=0.0, preferred_regions=None,
                                 max_share_supplier=1.0, max_share_per_plant_supplier=1.0,
                                 min_total_supplier=0.0, excluded_suppliers=None, min_quality_norm=0.0,
                                 region_min_shares=None, region_max_shares=None,
                                 ewt=0.0, max_total_emission=None):
    if preferred_regions is None: preferred_regions = []
    if excluded_suppliers is None: excluded_suppliers = []
    if region_min_shares is None: region_min_shares = {}
    if region_max_shares is None: region_max_shares = {}

    if plants_df is None or suppliers_df is None or ranking_df is None or plants_df.empty or suppliers_df.empty or ranking_df.empty:
        return pd.DataFrame(columns=['supplier_id','plant_id','quantity','region'])

    total_demand = float(plants_df['demand'].sum()) if len(plants_df)>0 else 0.0
    if total_demand<=0: return pd.DataFrame(columns=['supplier_id','plant_id','quantity','region'])

    q = ranking_df.set_index('supplier_id')['score']
    sup = suppliers_df.copy()
    sup = sup.join(q, on='supplier_id', rsuffix='_score')
    sup['score'] = sup['score'].fillna(sup['quality_score'] if 'quality_score' in sup.columns else 0.0)

    # normalize quality and compute region bonus
    max_score = sup['score'].max() or 1.0
    sup['Qn'] = sup['score']/max_score
    sup['region'] = sup.get('region', pd.Series([""]*len(sup))).fillna("")
    sup['region_bonus'] = sup['region'].isin(preferred_regions).astype(float)
    sup['emission_score'] = pd.to_numeric(sup.get('emission_score', 0.0), errors='coerce').fillna(0.0)

    # apply exclusions & quality floor by setting capacity 0
    sup = sup.copy()
    sup.loc[sup['supplier_id'].isin(excluded_suppliers), 'capacity'] = 0
    sup.loc[sup['Qn'] < float(min_quality_norm), 'capacity'] = 0

    plant_ids = plants_df['plant_id'].tolist()
    supplier_ids = sup['supplier_id'].tolist()

    prob = pulp.LpProblem("AllocationEnhanced", pulp.LpMaximize)
    x = {(s,p): pulp.LpVariable(f"x_{s}_{p}", lowBound=0) for s in supplier_ids for p in plant_ids}

    # Objective (maximize quality + region bonus - cost - emission penalty)
    prob += pulp.lpSum((qwt*sup.set_index('supplier_id').loc[s,'Qn']
                        + rwt*sup.set_index('supplier_id').loc[s,'region_bonus']
                        - cwt*sup.set_index('supplier_id').loc[s,'unit_cost']
                        - ewt*sup.set_index('supplier_id').loc[s,'emission_score']) * x[(s,p)]
                       for s in supplier_ids for p in plant_ids)

    # Demand per plant
    for p in plant_ids:
        prob += pulp.lpSum(x[(s,p)] for s in supplier_ids) >= float(plants_df.set_index('plant_id').loc[p,'demand'])

    # Capacity per supplier
    for s in supplier_ids:
        prob += pulp.lpSum(x[(s,p)] for p in plant_ids) <= float(sup.set_index('supplier_id').loc[s,'capacity'])

    # Global max share per supplier
    if max_share_supplier < 1.0:
        for s in supplier_ids:
            prob += pulp.lpSum(x[(s,p)] for p in plant_ids) <= max_share_supplier * total_demand

    # Max share per plant per supplier
    if max_share_per_plant_supplier < 1.0:
        for s in supplier_ids:
            for p in plant_ids:
                prob += x[(s,p)] <= max_share_per_plant_supplier * float(plants_df.set_index('plant_id').loc[p,'demand'])

    # Min total per supplier (absolute)
    if min_total_supplier > 0.0:
        for s in supplier_ids:
            prob += pulp.lpSum(x[(s,p)] for p in plant_ids) >= min_total_supplier

    # Region min/max shares (fractions of total demand)
    region_map = sup.set_index('supplier_id')['region'].to_dict()
    regions = set(region_map.values())
    for r in regions:
        idx = [s for s in supplier_ids if region_map.get(s,"")==r]
        if not idx: continue
        if r in region_min_shares and region_min_shares[r] is not None and region_min_shares[r] > 0:
            prob += pulp.lpSum(x[(s,p)] for s in idx for p in plant_ids) >= float(region_min_shares[r]) * total_demand
        if r in region_max_shares and region_max_shares[r] is not None and region_max_shares[r] < 1.0:
            prob += pulp.lpSum(x[(s,p)] for s in idx for p in plant_ids) <= float(region_max_shares[r]) * total_demand

    # Total emission cap (optional)
    if max_total_emission is not None:
        prob += pulp.lpSum(sup.set_index('supplier_id').loc[s,'emission_score'] * x[(s,p)]
                           for s in supplier_ids for p in plant_ids) <= float(max_total_emission)

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    rows = []
    for (s,p), var in x.items():
        val = var.value()
        if val and val>1e-6:
            rows.append(dict(supplier_id=s, plant_id=p, quantity=float(val), region=region_map.get(s,"")))
    return pd.DataFrame(rows).sort_values(['plant_id','supplier_id'])
