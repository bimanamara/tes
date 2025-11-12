
import pandas as pd, numpy as np
from .processing import hor_stage1, hor_stage2
def tornado_OAT(events, agents, R, E, actions, perturb=0.1):
    import pandas as pd
    if events is None or agents is None or R is None or E is None or actions is None or events.empty or agents.empty or R.empty or E.empty or actions.empty:
        return pd.DataFrame(columns=['parameter','base','new','delta'])

    base_w, base_ARP = hor_stage1(events, agents, R)
    base_detail = hor_stage2(E, base_ARP, actions)
    base_score = float(base_detail['TE'].sum())
    rows = []
    for e in events['event_id']:
        e_df = events.copy(); e_df.loc[e_df['event_id']==e, 'severity'] *= (1+perturb)
        w, a = hor_stage1(e_df, agents, R); d2 = hor_stage2(E, a, actions)
        rows.append(dict(parameter=f"severity:{e}", base=base_score, new=float(d2['TE'].sum())))
    for a in agents['agent_id']:
        ag_df = agents.copy(); ag_df.loc[ag_df['agent_id']==a, 'occurrence'] *= (1+perturb)
        w, a2 = hor_stage1(events, ag_df, R); d2 = hor_stage2(E, a2, actions)
        rows.append(dict(parameter=f"occurrence:{a}", base=base_score, new=float(d2['TE'].sum())))
    df = pd.DataFrame(rows); df['delta'] = (df['new'] - df['base']).abs()
    return df.sort_values('delta', ascending=False)
