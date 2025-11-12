
import pandas as pd, numpy as np, pulp
def optimize_allocation(plants_df: pd.DataFrame, suppliers_df: pd.DataFrame, ranking_df: pd.DataFrame, qwt=1.0, cwt=0.0):
    if plants_df is None or suppliers_df is None or ranking_df is None or plants_df.empty or suppliers_df.empty or ranking_df.empty:
        return pd.DataFrame(columns=['supplier_id','plant_id','quantity'])

    q = ranking_df.set_index('supplier_id')['score']
    sup = suppliers_df.copy().join(q, on='supplier_id', rsuffix='_score')
    sup['score'] = sup['score'].fillna(sup['quality_score'] if 'quality_score' in sup.columns else 0.0)
    max_score = sup['score'].max() or 1.0
    sup['Qn'] = sup['score']/max_score
    plant_ids = plants_df['plant_id'].tolist(); supplier_ids = sup['supplier_id'].tolist()
    prob = pulp.LpProblem("Allocation", pulp.LpMaximize)
    x = {(s,p): pulp.LpVariable(f"x_{s}_{p}", lowBound=0) for s in supplier_ids for p in plant_ids}
    prob += pulp.lpSum((qwt*sup.set_index('supplier_id').loc[s,'Qn'] - cwt*sup.set_index('supplier_id').loc[s,'unit_cost']) * x[(s,p)]
                       for s in supplier_ids for p in plant_ids)
    for p in plant_ids:
        prob += pulp.lpSum(x[(s,p)] for s in supplier_ids) >= float(plants_df.set_index('plant_id').loc[p,'demand'])
    for s in supplier_ids:
        prob += pulp.lpSum(x[(s,p)] for p in plant_ids) <= float(sup.set_index('supplier_id').loc[s,'capacity'])
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    rows = []
    for (s,p), var in x.items():
        val = var.value()
        if val and val>1e-6:
            rows.append(dict(supplier_id=s, plant_id=p, quantity=float(val)))
    return pd.DataFrame(rows).sort_values(['plant_id','supplier_id'])
