# app/modules/optimizer.py
import pandas as pd
import numpy as np
import pulp


def _coerce_numeric_cols(df: pd.DataFrame, cols):
    """Pastikan kolom numerik valid; NaN -> 0."""
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
        else:
            # jika kolom tidak ada, tambahkan kolom nol agar aman
            df[c] = 0.0
    return df


def _lp_value(var):
    """Ambil nilai variabel pulp secara aman (None -> 0.0)."""
    try:
        v = var.value()
        return float(v) if v is not None else 0.0
    except Exception:
        return 0.0


def weighted_sum_selection(
    detail: pd.DataFrame,
    budget_cost: float,
    budget_mh: float,
    w_te: float = 1.0,
    w_cost: float = 0.0,
    w_mh: float = 0.0,
):
    """
    Pilih aksi (biner) memaksimalkan: w_te*TE - w_cost*Cost - w_mh*Manhours
    s.t. Cost <= budget_cost, Manhours <= budget_mh
    """
    if detail is None or len(detail) == 0:
        return pd.DataFrame(columns=["TE", "Cost", "manhours"]), dict(
            TE=0.0, Cost=0.0, Manhours=0.0
        )

    # pastikan kolom penting ada & numerik
    detail = _coerce_numeric_cols(detail, ["TE", "Cost", "manhours"])
    # pastikan index unik dan berupa label aksi
    if detail.index.name is None:
        detail = detail.copy()
        detail.index.name = "action_id"

    prob = pulp.LpProblem("ActionSelect", pulp.LpMaximize)
    x = {k: pulp.LpVariable(str(k), lowBound=0, upBound=1, cat="Binary") for k in detail.index}

    TE = pulp.lpSum(detail.loc[k, "TE"] * x[k] for k in detail.index)
    C = pulp.lpSum(detail.loc[k, "Cost"] * x[k] for k in detail.index)
    MH = pulp.lpSum(detail.loc[k, "manhours"] * x[k] for k in detail.index)

    prob += w_te * TE - w_cost * C - w_mh * MH
    prob += C <= float(budget_cost)
    prob += MH <= float(budget_mh)

    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus.get(prob.status, "Unknown")

    # Kalau infeasible, kembalikan kosong tapi aman
    if status not in ("Optimal", "Feasible"):
        return pd.DataFrame(columns=["TE", "Cost", "manhours"]), dict(
            TE=0.0, Cost=0.0, Manhours=0.0, status=status
        )

    sel = [k for k, v in x.items() if _lp_value(v) >= 0.99]
    out = detail.loc[sel].copy() if len(sel) else detail.iloc[0:0].copy()

    return out, dict(
        TE=float(out["TE"].sum()) if len(out) else 0.0,
        Cost=float(out["Cost"].sum()) if len(out) else 0.0,
        Manhours=float(out["manhours"].sum()) if len(out) else 0.0,
        status=status,
    )


def epsilon_constraint_TE(
    detail: pd.DataFrame, budget_cost: float, budget_mh: float, te_targets
) -> pd.DataFrame:
    """
    Frontier epsilon-constraint: untuk tiap target TE, minimalkan Cost
    s.t. TE >= target, Cost <= budget_cost, MH <= budget_mh.
    Mengembalikan DataFrame: [target_TE, status, TE, Cost, MH, actions]
    """
    if detail is None or len(detail) == 0:
        return pd.DataFrame(
            columns=["target_TE", "status", "TE", "Cost", "MH", "actions"]
        )

    detail = _coerce_numeric_cols(detail, ["TE", "Cost", "manhours"])
    if detail.index.name is None:
        detail = detail.copy()
        detail.index.name = "action_id"

    # normalisasi list target
    if te_targets is None:
        te_targets = []
    if not isinstance(te_targets, (list, tuple, np.ndarray, pd.Series)):
        te_targets = [te_targets]
    te_targets = [float(t) for t in te_targets]

    solutions = []
    for te in te_targets:
        prob = pulp.LpProblem("Epsilon", pulp.LpMaximize)
        x = {k: pulp.LpVariable(str(k), lowBound=0, upBound=1, cat="Binary") for k in detail.index}

        TE = pulp.lpSum(detail.loc[k, "TE"] * x[k] for k in detail.index)
        C = pulp.lpSum(detail.loc[k, "Cost"] * x[k] for k in detail.index)
        MH = pulp.lpSum(detail.loc[k, "manhours"] * x[k] for k in detail.index)

        # Minimasi biaya → maksimasi -C
        prob += -C
        prob += TE >= float(te)
        prob += MH <= float(budget_mh)
        prob += C <= float(budget_cost)

        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        status = pulp.LpStatus.get(prob.status, "Unknown")

        sel = [k for k, v in x.items() if _lp_value(v) >= 0.99]
        if status in ("Optimal", "Feasible") and len(sel) > 0:
            TE_val = float(detail.loc[sel, "TE"].sum())
            C_val = float(detail.loc[sel, "Cost"].sum())
            MH_val = float(detail.loc[sel, "manhours"].sum())
            acts = ",".join(map(str, sel))
        else:
            # infeasible / kosong → isi aman
            TE_val, C_val, MH_val, acts = (0.0, np.nan, np.nan, "")

        solutions.append(
            dict(
                target_TE=float(te),
                status=status,
                TE=TE_val,
                Cost=C_val,
                MH=MH_val,
                actions=acts,
            )
        )

    df = pd.DataFrame(solutions)
    # urutkan: feasible dulu (biaya kecil ke besar), lalu infeasible
    if "Cost" in df.columns:
        df_feas = df[df["status"].isin(["Optimal", "Feasible"])].sort_values("Cost", na_position="last")
        df_infeas = df[~df["status"].isin(["Optimal", "Feasible"])]
        df = pd.concat([df_feas, df_infeas], ignore_index=True)
    return df
