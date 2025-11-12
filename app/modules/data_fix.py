
import pandas as pd, numpy as np
from pathlib import Path
from datetime import datetime

def _log(entries, file, level, msg):
    entries.append(dict(file=file, level=level, message=msg))

def _coerce_numeric(df, cols, clip=None, nonneg=None):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    if clip:
        lo, hi = clip
        for c in cols:
            if c in df.columns:
                df[c] = df[c].clip(lo, hi)
    if nonneg:
        for c in cols:
            if c in df.columns:
                df[c] = df[c].clip(lower=0)
    return df

def fix_all(tpl: Path, backup_dir: Path):
    log = []
    backup_path = backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_path.mkdir(parents=True, exist_ok=True)

    # helper read/write with backup
    def rd(name, **kw):
        p = tpl/name
        if not p.exists():
            _log(log, name, "WARN", "missing file (skipped)")
            return None
        try:
            df = pd.read_csv(p, **kw)
            # backup original
            df.to_csv(backup_path/f"{name}.orig.csv", index=kw.get("index_col", None) is not None)
            return df
        except Exception as e:
            _log(log, name, "ERROR", f"read error: {e}")
            return None

    def wr(name, df, index=False):
        if df is None: return
        df.to_csv(tpl/name, index=index)
        _log(log, name, "OK", f"fixed & saved ({len(df)} rows × {len(df.columns)} cols)")

    # load masters
    events = rd("hor_events.csv")
    agents = rd("hor_agents.csv")
    R = rd("hor_R.csv", index_col=0)
    actions = rd("hor_actions.csv")
    if actions is not None and "action_id" in actions.columns:
        actions = actions.drop_duplicates("action_id").set_index("action_id")
    E = rd("hor_effectiveness.csv", index_col=0)
    respondents = rd("respondents.csv")
    criteria = rd("criteria.csv")
    subcriteria = rd("subcriteria.csv")
    edges = rd("dematel_edges.csv")
    suppliers = rd("suppliers.csv")
    ratings = rd("supplier_ratings.csv")

    # 1) Trim whitespace for ID-like columns
    def trim_cols(df, cols):
        if df is None: return df
        for c in cols:
            if c in df.columns:
                df[c] = df[c].astype(str).str.strip()
        return df

    events = trim_cols(events, ["event_id","name","description"])
    agents = trim_cols(agents, ["agent_id","name"])
    actions = trim_cols(actions.reset_index(), ["action_id","name"]).set_index("action_id") if actions is not None else None
    respondents = trim_cols(respondents, ["respondent_id","name","role"])
    criteria = trim_cols(criteria, ["criterion_id","name"])
    subcriteria = trim_cols(subcriteria, ["sub_id","name","criterion_id"])
    edges = trim_cols(edges, ["respondent_id","from_sub","to_sub"])
    suppliers = trim_cols(suppliers, ["supplier_id","name","region"])
    ratings = trim_cols(ratings, ["supplier_id","sub_id","respondent_id","plant_id","time_period","cheese_type"])

    # 2) Drop duplicates on primary IDs
    def dedup(df, key, file):
        if df is None or key not in df.columns: return df
        before = len(df)
        df = df.drop_duplicates(key)
        after = len(df)
        if after < before:
            _log(log, file, "WARN", f"dropped {before-after} duplicate {key}")
        return df
    events = dedup(events, "event_id", "hor_events.csv")
    agents = dedup(agents, "agent_id", "hor_agents.csv")
    if actions is not None:
        before = len(actions); actions = actions[~actions.index.duplicated(keep="first")]; 
        if len(actions)<before: _log(log,"hor_actions.csv","WARN",f"dropped {before-len(actions)} duplicate action_id")
    respondents = dedup(respondents, "respondent_id", "respondents.csv")
    criteria = dedup(criteria, "criterion_id", "criteria.csv")
    subcriteria = dedup(subcriteria, "sub_id", "subcriteria.csv")
    suppliers = dedup(suppliers, "supplier_id", "suppliers.csv")

    # 3) Coerce numeric & clip ranges
    events = _coerce_numeric(events, ["severity"], clip=(1,10))
    agents = _coerce_numeric(agents, ["occurrence"], clip=(1,10))
    if actions is not None:
        actions = _coerce_numeric(actions, ["difficulty"], clip=(1,5))
        actions = _coerce_numeric(actions, ["cost","manhours"], nonneg=True)
    respondents = _coerce_numeric(respondents, ["weight"], nonneg=True)
    if R is not None:
        R = R.apply(pd.to_numeric, errors="coerce").fillna(0).clip(0,3).astype(int)
    if E is not None:
        E = E.apply(pd.to_numeric, errors="coerce").fillna(0.0).clip(0.0,1.0)

    # 4) Referential integrity, reindex/restrict matrices
    if R is not None and events is not None and agents is not None:
        ev = events["event_id"].tolist()
        ag = agents["agent_id"].tolist()
        # take intersection/union? We'll reindex to master lists, filling 0
        R = R.reindex(index=ev, columns=ag, fill_value=0)
        _log(log, "hor_R.csv", "OK", "reindexed to events×agents (missing filled 0)")
    if E is not None and agents is not None and actions is not None:
        ag = agents["agent_id"].tolist()
        ac = actions.index.tolist()
        E = E.reindex(index=ag, columns=ac, fill_value=0.0)
        _log(log, "hor_effectiveness.csv", "OK", "reindexed to agents×actions (missing filled 0)")
    if subcriteria is not None and criteria is not None and "criterion_id" in subcriteria.columns:
        # fix any invalid criterion_id by mapping to first criterion
        valid = set(criteria["criterion_id"].tolist())
        bad = ~subcriteria["criterion_id"].isin(valid)
        if bad.any() and len(valid)>0:
            first = next(iter(valid))
            subcriteria.loc[bad, "criterion_id"] = first
            _log(log, "subcriteria.csv", "WARN", f"fixed {bad.sum()} invalid criterion_id to {first}")
    if edges is not None:
        if respondents is not None:
            edges = edges[edges["respondent_id"].isin(respondents["respondent_id"])]
        if subcriteria is not None:
            edges = edges[edges["from_sub"].isin(subcriteria["sub_id"]) & edges["to_sub"].isin(subcriteria["sub_id"])]
        # coerce score 0..4
        edges["score"] = pd.to_numeric(edges.get("score", 0), errors="coerce").fillna(0).clip(0,4)
    if ratings is not None:
        if suppliers is not None:
            ratings = ratings[ratings["supplier_id"].isin(suppliers["supplier_id"])]
        if subcriteria is not None:
            ratings = ratings[ratings["sub_id"].isin(subcriteria["sub_id"])]
        if respondents is not None:
            ratings = ratings[ratings["respondent_id"].isin(respondents["respondent_id"])]
        ratings["rating"] = pd.to_numeric(ratings.get("rating", 0), errors="coerce").fillna(0).clip(1,5)

    # 5) Write back
    wr("hor_events.csv", events)
    wr("hor_agents.csv", agents)
    if R is not None: R.to_csv(tpl/"hor_R.csv")
    if actions is not None: actions.reset_index().to_csv(tpl/"hor_actions.csv", index=False)
    if E is not None: E.to_csv(tpl/"hor_effectiveness.csv")
    wr("respondents.csv", respondents)
    wr("criteria.csv", criteria)
    wr("subcriteria.csv", subcriteria)
    wr("dematel_edges.csv", edges)
    wr("suppliers.csv", suppliers)
    wr("supplier_ratings.csv", ratings)

    return pd.DataFrame(log)
