# app/modules/mapper_smart.py

import streamlit as st
import pandas as pd
import re
from difflib import SequenceMatcher
from pathlib import Path

__all__ = ["smart_map_columns_ui"]

SCHEMAS = {
    "hor_events.csv": ["event_id", "name", "description", "severity"],
    "hor_agents.csv": ["agent_id", "name", "occurrence"],
    "hor_actions.csv": ["action_id", "name", "difficulty", "cost", "manhours"],
    "respondents.csv": ["respondent_id", "name", "role", "weight"],
    "criteria.csv": ["criterion_id", "name"],
    "subcriteria.csv": ["sub_id", "name", "criterion_id"],
    "dematel_edges.csv": ["respondent_id", "from_sub", "to_sub", "score"],
    "suppliers.csv": ["supplier_id", "name", "region"],
    "supplier_ratings.csv": ["supplier_id", "sub_id", "respondent_id", "rating", "plant_id", "time_period", "cheese_type"],
    "allocation_plants.csv": ["plant_id", "demand"],
    "allocation_suppliers.csv": ["supplier_id", "capacity", "unit_cost", "quality_score"],
}

ALIASES = {
    "event_id": ["event", "id_event", "eventid", "risk_id", "id_risk"],
    "agent_id": ["agent", "id_agent", "agentid", "cause_id", "id_cause"],
    "action_id": ["action", "mitigation", "id_action", "actionid"],
    "respondent_id": ["respondent", "expert", "id_respondent", "person_id", "rater_id"],
    "criterion_id": ["criterion", "criteria_id", "id_criterion"],
    "sub_id": ["sub", "subcriterion", "sub_criterion", "subcriteria_id"],
    "supplier_id": ["supplier", "vendor", "id_supplier", "supplierid", "vendor_id"],
    "severity": ["impact", "severity_score", "sev"],
    "occurrence": ["frequency", "likelihood", "probability", "occ"],
    "difficulty": ["effort", "complexity", "difficulty_score"],
    "cost": ["price", "budget"],
    "manhours": ["mh", "man_hour", "man_hours", "hours", "workhours"],
    "weight": ["bobot", "importance"],
    "score": ["influence", "degree"],
    "rating": ["score", "nilai"],
    "plant_id": ["plant", "site", "factory"],
    "time_period": ["period", "periode", "time", "quarter", "month"],
    "cheese_type": ["product", "sku", "item", "category", "jenis_keju"],
    "capacity": ["cap", "max_supply"],
    "unit_cost": ["unitprice", "unit_price", "cost_per_unit"],
    "quality_score": ["qscore", "quality", "qualityindex"],
}

def _norm(s: str) -> str:
    s = str(s).strip().lower()
    return re.sub(r"[^a-z0-9]+", "", s)

def _sim_score(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()

def smart_map_columns_ui(tpl_dir: Path, key_prefix: str = "smart_mapper"):
    """Smart Column Mapper (fuzzy) — sarankan mapping otomatis lalu izinkan override."""
    st.subheader("🧠 Smart Column Mapper")

    if not isinstance(tpl_dir, (str, Path)):
        st.warning("Direktori template tidak valid.")
        return
    tpl_dir = Path(tpl_dir)

    fname = st.selectbox(
        "Pilih file untuk auto-map kolom",
        sorted(SCHEMAS.keys()),
        key=f"{key_prefix}_file"
    )
    p = tpl_dir / fname
    if not p.exists():
        st.warning("File belum ada. Upload dulu lewat Data Wizard atau generate dummy data.")
        return

    try:
        df = pd.read_csv(p)
    except Exception as e:
        st.error(f"Gagal membaca {fname}: {e}")
        return

    st.caption(f"Kolom saat ini: {list(df.columns)}")
    required = SCHEMAS[fname]

    # Buat saran mapping otomatis
    suggestions = {}
    for target in required:
        best, best_sc = None, -1.0
        for col in df.columns:
            sc = _sim_score(target, col)
            if sc > best_sc:
                best, best_sc = col, sc
        # cek alias dengan sedikit boost
        for alias in ALIASES.get(target, []):
            for col in df.columns:
                sc = _sim_score(alias, col) + 0.05
                if sc > best_sc:
                    best, best_sc = col, sc
        suggestions[target] = best if best_sc > 0.45 else None  # threshold

    st.write("Saran otomatis mapping (bisa diubah):")
    chosen = {}
    options = ["<skip>"] + list(df.columns)
    for target in required:
        idx = 0
        if suggestions[target] in df.columns:
            idx = 1 + list(df.columns).index(suggestions[target])
        chosen[target] = st.selectbox(
            target,
            options,
            index=idx,
            key=f"{key_prefix}_{fname}_{target}"
        )

    if st.button("Apply Smart Mapping & Save", key=f"{key_prefix}_apply_{fname}"):
        # Rename kolom sesuai pilihan; yang <skip> diabaikan
        rename = {
            src: tgt for tgt, src in chosen.items()
            if src in df.columns and src != "<skip>"
        }
        df2 = df.rename(columns=rename)

        # Pastikan semua kolom wajib ada; kalau tidak, tambahkan kolom kosong
        for target in required:
            if target not in df2.columns:
                df2[target] = None

        # Reorder: kolom wajib dulu, sisanya di belakang
        df2 = df2[required + [c for c in df2.columns if c not in required]]

        try:
            df2.to_csv(p, index=False)
            st.success(f"Smart mapping applied & saved to {fname}.")
            st.dataframe(df2.head())
        except Exception as e:
            st.error(f"Gagal menyimpan {fname}: {e}")
