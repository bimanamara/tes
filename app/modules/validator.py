
import pandas as pd, numpy as np
from pathlib import Path

def _ok(file, msg): return dict(file=file, level="OK", message=msg)
def _warn(file, msg): return dict(file=file, level="WARN", message=msg)
def _err(file, msg): return dict(file=file, level="ERROR", message=msg)

def validate_all(tpl: Path):
    rep = []
    # helper to read
    def rd(name, **kw):
        p = tpl/name
        if not p.exists(): return None, [_err(name, "missing file")]
        try:
            return pd.read_csv(p, **kw), []
        except Exception as e:
            return None, [_err(name, f"read error: {e}")]
    # load
    events, r1 = rd("hor_events.csv"); agents, r2 = rd("hor_agents.csv")
    R, r3 = rd("hor_R.csv", index_col=0); actions, r4 = rd("hor_actions.csv")
    if actions is not None: actions = actions.set_index("action_id")
    E, r5 = rd("hor_effectiveness.csv", index_col=0)
    respondents, r6 = rd("respondents.csv"); criteria, r7 = rd("criteria.csv")
    subcriteria, r8 = rd("subcriteria.csv"); edges, r9 = rd("dematel_edges.csv")
    suppliers, r10 = rd("suppliers.csv"); ratings, r11 = rd("supplier_ratings.csv")
    for r in [r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11]: rep += r

    # if major missing, return early
    if any(x['level']=="ERROR" and "missing" in x['message'] for x in rep):
        return pd.DataFrame(rep)

    # uniqueness checks
    def uniq(df, col, file):
        if df is None or col not in df.columns: 
            rep.append(_err(file, f"missing column: {col}")); return
        dups = df[col][df[col].duplicated()]
        if len(dups): rep.append(_err(file, f"duplicate IDs in {col}: {sorted(dups.unique())[:5]}"))
        else: rep.append(_ok(file, f"unique {col} ✅"))
    uniq(events, "event_id", "hor_events.csv")
    uniq(agents, "agent_id", "hor_agents.csv")
    uniq(actions.reset_index(), "action_id", "hor_actions.csv")
    uniq(respondents, "respondent_id", "respondents.csv")
    uniq(criteria, "criterion_id", "criteria.csv")
    uniq(subcriteria, "sub_id", "subcriteria.csv")
    uniq(suppliers, "supplier_id", "suppliers.csv")

    # range checks
    if events is not None and "severity" in events.columns:
        bad = events[~events["severity"].between(1,10, inclusive="both")]
        if len(bad): rep.append(_err("hor_events.csv", f"severity out of [1..10]: {len(bad)} rows")); 
        else: rep.append(_ok("hor_events.csv", "severity in [1..10]"))
    if agents is not None and "occurrence" in agents.columns:
        bad = agents[~agents["occurrence"].between(1,10, inclusive="both")]
        if len(bad): rep.append(_err("hor_agents.csv", f"occurrence out of [1..10]: {len(bad)} rows"))
        else: rep.append(_ok("hor_agents.csv", "occurrence in [1..10]"))
    if actions is not None:
        if "difficulty" in actions.columns:
            bad = actions[~actions["difficulty"].between(1,5, inclusive="both")]
            rep.append(_err("hor_actions.csv", f"difficulty out of [1..5]: {len(bad)} rows") if len(bad) else _ok("hor_actions.csv","difficulty in [1..5]"))
        if "cost" in actions.columns:
            bad = actions[actions["cost"]<0]; rep.append(_err("hor_actions.csv", f"cost < 0: {len(bad)}") if len(bad) else _ok("hor_actions.csv", "cost >= 0"))
        if "manhours" in actions.columns:
            bad = actions[actions["manhours"]<0]; rep.append(_err("hor_actions.csv", f"manhours < 0: {len(bad)}") if len(bad) else _ok("hor_actions.csv", "manhours >= 0"))
    if respondents is not None and "weight" in respondents.columns:
        bad = respondents[respondents["weight"]<=0]; rep.append(_err("respondents.csv","weight must be > 0") if len(bad) else _ok("respondents.csv","weight > 0"))
    if edges is not None and "score" in edges.columns:
        bad = edges[~edges["score"].between(0,4, inclusive="both")]
        rep.append(_err("dematel_edges.csv", f"score out of [0..4]: {len(bad)}") if len(bad) else _ok("dematel_edges.csv", "score in [0..4]"))
    # matrix ranges
    if R is not None:
        try:
            b = (R.values>=0)&(R.values<=3)
            if not b.all(): rep.append(_err("hor_R.csv", "values must be 0..3"))
            else: rep.append(_ok("hor_R.csv", "values in 0..3"))
        except Exception as e:
            rep.append(_err("hor_R.csv", f"value check error: {e}"))
    if E is not None:
        try:
            b = (E.values>=0)&(E.values<=1)
            if not b.all(): rep.append(_err("hor_effectiveness.csv", "values must be 0..1"))
            else: rep.append(_ok("hor_effectiveness.csv", "values in 0..1"))
        except Exception as e:
            rep.append(_err("hor_effectiveness.csv", f"value check error: {e}"))

    # referential integrity
    # R: rows=events, cols=agents
    if R is not None and events is not None and agents is not None:
        miss_rows = [i for i in R.index if i not in events["event_id"].tolist()]
        miss_cols = [c for c in R.columns if c not in agents["agent_id"].tolist()]
        if miss_rows: rep.append(_err("hor_R.csv", f"row IDs not in events: {miss_rows[:5]}"))
        if miss_cols: rep.append(_err("hor_R.csv", f"column IDs not in agents: {miss_cols[:5]}"))
        if not miss_rows and not miss_cols: rep.append(_ok("hor_R.csv", "IDs aligned with events×agents"))
    # E: rows=agents, cols=actions
    if E is not None and agents is not None and actions is not None:
        miss_rows = [i for i in E.index if i not in agents["agent_id"].tolist()]
        miss_cols = [c for c in E.columns if c not in actions.index.tolist()]
        if miss_rows: rep.append(_err("hor_effectiveness.csv", f"row IDs not in agents: {miss_rows[:5]}"))
        if miss_cols: rep.append(_err("hor_effectiveness.csv", f"column IDs not in actions: {miss_cols[:5]}"))
        if not miss_rows and not miss_cols: rep.append(_ok("hor_effectiveness.csv", "IDs aligned with agents×actions"))
    # subcriteria criterion_id exists
    if subcriteria is not None and criteria is not None:
        bad = subcriteria[~subcriteria["criterion_id"].isin(criteria["criterion_id"])]
        rep.append(_err("subcriteria.csv", f"criterion_id not found: {len(bad)}") if len(bad) else _ok("subcriteria.csv", "criterion_id OK"))
    # dematel_edges respondent/sub ids exist
    if edges is not None and respondents is not None and subcriteria is not None:
        bad_r = edges[~edges["respondent_id"].isin(respondents["respondent_id"])]
        bad_s1 = edges[~edges["from_sub"].isin(subcriteria["sub_id"])]
        bad_s2 = edges[~edges["to_sub"].isin(subcriteria["sub_id"])]
        if len(bad_r): rep.append(_err("dematel_edges.csv", f"respondent_id not found: {len(bad_r)}"))
        if len(bad_s1): rep.append(_err("dematel_edges.csv", f"from_sub not found: {len(bad_s1)}"))
        if len(bad_s2): rep.append(_err("dematel_edges.csv", f"to_sub not found: {len(bad_s2)}"))
        if len(bad_r)==0 and len(bad_s1)==0 and len(bad_s2)==0: rep.append(_ok("dematel_edges.csv", "IDs OK"))
    # supplier_ratings FK checks
    if ratings is not None and suppliers is not None and subcriteria is not None and respondents is not None:
        bad1 = ratings[~ratings["supplier_id"].isin(suppliers["supplier_id"])]
        bad2 = ratings[~ratings["sub_id"].isin(subcriteria["sub_id"])]
        bad3 = ratings[~ratings["respondent_id"].isin(respondents["respondent_id"])]
        if len(bad1): rep.append(_err("supplier_ratings.csv", f"supplier_id not found: {len(bad1)}"))
        if len(bad2): rep.append(_err("supplier_ratings.csv", f"sub_id not found: {len(bad2)}"))
        if len(bad3): rep.append(_err("supplier_ratings.csv", f"respondent_id not found: {len(bad3)}"))
        if len(bad1)==0 and len(bad2)==0 and len(bad3)==0: rep.append(_ok("supplier_ratings.csv", "FK OK"))

    # warn if any empty tables
    targets = [("hor_events.csv", events),("hor_agents.csv", agents),("hor_R.csv", R),("hor_actions.csv", actions),
               ("hor_effectiveness.csv", E),("respondents.csv", respondents),("criteria.csv", criteria),
               ("subcriteria.csv", subcriteria),("dematel_edges.csv", edges),("suppliers.csv", suppliers),("supplier_ratings.csv", ratings)]
    for fname, df in targets:
        if df is None or (hasattr(df, "empty") and df.empty):
            rep.append(_warn(fname, "file is empty"))

    return pd.DataFrame(rep)
