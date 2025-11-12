import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional

def safe_reindex(df: pd.DataFrame, index=None, columns=None, fill=0):
    """Safely reindex DataFrame with fill values"""
    if df is None or df.empty:
        if index is not None and columns is not None:
            return pd.DataFrame(fill, index=index, columns=columns)
        return pd.DataFrame()
    
    out = df.copy()
    
    if index is not None:
        if not isinstance(index, pd.Index):
            index = pd.Index(index)
        out = out.reindex(index=index, fill_value=fill)
    
    if columns is not None:
        if not isinstance(columns, pd.Index):
            columns = pd.Index(columns)
        out = out.reindex(columns=columns, fill_value=fill)
    
    return out


def hor_stage1(events: pd.DataFrame, agents: pd.DataFrame, R: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    HOR Stage 1: Calculate weighted S×R matrix and ARP
    
    Returns:
        Tuple of (weighted matrix, ARP series)
    """
    # Validate inputs
    if events is None or agents is None or R is None:
        return pd.DataFrame(), pd.Series(dtype=float)
    
    if events.empty or agents.empty or R.empty:
        return pd.DataFrame(), pd.Series(dtype=float)
    
    try:
        # Extract severity and occurrence
        sev = events.set_index('event_id')['severity'].astype(float)
        occ = agents.set_index('agent_id')['occurrence'].astype(float)
        
        # Ensure R is aligned
        R = safe_reindex(R, index=sev.index, columns=occ.index, fill=0)
        
        # Calculate weighted matrix
        weighted = R.mul(sev, axis=0)
        
        # Calculate ARP
        ARP = (weighted.sum(axis=0) * occ)
        
        return weighted, ARP
    
    except Exception as e:
        print(f"Error in hor_stage1: {e}")
        return pd.DataFrame(), pd.Series(dtype=float)


def hor_stage2(E, ARP, actions):
    import numpy as np
    import pandas as pd

    # Guard: kalau input kosong, kembalikan frame kosong dengan schema yang benar
    if (E is None or E.empty or
        actions is None or actions.empty or
        ARP is None or ARP.size == 0):
        return pd.DataFrame(columns=['TE','Difficulty','Cost','manhours','ETD'])

    # --- Inti perbaikan: orientasi & penyelarasan indeks ---
    # Asumsi: E = aksi x agen, ARP = per agen
    E2 = E.reindex(columns=ARP.index, fill_value=0)             # selaraskan kolom E ke agen (ARP)
    TE = E2.mul(ARP, axis=1).sum(axis=1)                        # kalikan per kolom (agen) → jumlahkan per baris (aksi)
    TE.name = 'TE'

    # Pastikan kolom2 aksi tersedia (isi default bila tidak ada)
    if 'difficulty' not in actions.columns: actions['difficulty'] = 1.0
    if 'cost' not in actions.columns:       actions['cost'] = 0.0
    if 'manhours' not in actions.columns:   actions['manhours'] = 0.0

    # Susun detail ter-align ke index aksi
    idx_actions = actions.index
    detail = pd.DataFrame(index=idx_actions)
    detail['TE']        = TE.reindex(idx_actions).fillna(0)
    detail['Difficulty']= pd.to_numeric(actions['difficulty'], errors='coerce').fillna(1.0).clip(lower=1e-9)
    detail['Cost']      = pd.to_numeric(actions['cost'],       errors='coerce').fillna(0.0)
    detail['manhours']  = pd.to_numeric(actions['manhours'],   errors='coerce').fillna(0.0)

    detail['ETD'] = detail['TE'] / detail['Difficulty']
    return detail.sort_values('ETD', ascending=False)

def build_dematel(respondents: pd.DataFrame, subcriteria: pd.DataFrame, 
                  edges: pd.DataFrame) -> Dict:
    """
    Build DEMATEL matrices
    
    Returns:
        Dict with A, X, I, ImX, ImX_inv, T, r, c, alpha
    """
    # Initialize empty result
    empty_result = {
        'A': pd.DataFrame(),
        'X': pd.DataFrame(),
        'I': pd.DataFrame(),
        'ImX': pd.DataFrame(),
        'ImX_inv': pd.DataFrame(),
        'T': pd.DataFrame(),
        'r': pd.Series(dtype=float),
        'c': pd.Series(dtype=float),
        'alpha': 1.0
    }
    
    if subcriteria is None or subcriteria.empty:
        return empty_result
    
    if respondents is None or respondents.empty:
        return empty_result
    
    if edges is None or edges.empty:
        return empty_result
    
    try:
        # Get subcriteria list
        subs = subcriteria['sub_id'].tolist()
        
        # Initialize matrices
        A = pd.DataFrame(0.0, index=subs, columns=subs)
        CNT = pd.DataFrame(0.0, index=subs, columns=subs)
        
        # Get respondent weights
        wmap = dict(zip(
            respondents['respondent_id'],
            respondents.get('weight', 1.0)
        ))
        
        # Build average influence matrix A
        for _, r in edges.iterrows():
            i, j = r['from_sub'], r['to_sub']
            
            # Skip self-influence and invalid indices
            if i == j or i not in A.index or j not in A.columns:
                continue
            
            s = float(r.get('score', 0))
            w = float(wmap.get(r['respondent_id'], 1.0))
            
            A.at[i, j] += s * w
            CNT.at[i, j] += w
        
        # Average by weight count
        A = A.divide(CNT.replace(0, np.nan)).fillna(0.0)
        
        # Normalize with alpha
        row_max = A.sum(axis=1).max()
        col_max = A.sum(axis=0).max()
        max_val = max(row_max, col_max)
        
        alpha = 1.0 / max_val if max_val > 0 else 1.0
        
        X = A * alpha
        
        # Identity matrix
        n = X.shape[0]
        I = pd.DataFrame(np.eye(n), index=X.index, columns=X.columns)
        
        # (I - X)
        ImX = I - X
        
        # (I - X)^-1
        try:
            ImX_inv = pd.DataFrame(
                np.linalg.inv(ImX.values),
                index=X.index,
                columns=X.columns
            )
        except np.linalg.LinAlgError:
            # Singular matrix - use pseudo-inverse
            ImX_inv = pd.DataFrame(
                np.linalg.pinv(ImX.values),
                index=X.index,
                columns=X.columns
            )
        
        # Total relation matrix T = X(I-X)^-1
        T = X @ ImX_inv
        
        # Calculate r and c
        r = T.sum(axis=1)
        c = T.sum(axis=0)
        
        return {
            'A': A,
            'X': X,
            'I': I,
            'ImX': ImX,
            'ImX_inv': ImX_inv,
            'T': T,
            'r': r,
            'c': c,
            'alpha': alpha
        }
    
    except Exception as e:
        print(f"Error in build_dematel: {e}")
        return empty_result


def danp_from_T(subcriteria: pd.DataFrame, criteria: pd.DataFrame, 
                T: pd.DataFrame) -> Dict:
    """
    Calculate DANP weights from DEMATEL total relation matrix
    
    Returns:
        Dict with T_alpha_c, W_un, Td, T_alpha_d, W_alpha, W_limit, gw
    """
    # Initialize empty result
    empty_result = {
        'T_alpha_c': pd.DataFrame(),
        'W_un': pd.DataFrame(),
        'Td': pd.DataFrame(),
        'T_alpha_d': pd.DataFrame(),
        'W_alpha': pd.DataFrame(),
        'W_limit': pd.DataFrame(),
        'gw': pd.Series(dtype=float)
    }
    
    if T is None or T.empty:
        return empty_result
    
    if subcriteria is None or subcriteria.empty:
        return empty_result
    
    if criteria is None or criteria.empty:
        return empty_result
    
    try:
        subs = subcriteria['sub_id'].tolist()
        crits = criteria['criterion_id'].tolist()
        
        # T_alpha_c: normalize T by row sums within criteria
        T_alpha_c = T.copy()
        
        for crit in crits:
            rows = subcriteria.loc[
                subcriteria['criterion_id'] == crit, 'sub_id'
            ].tolist()
            
            if rows:
                row_sum = T.loc[rows, :].sum(axis=1).replace(0, 1.0)
                T_alpha_c.loc[rows, :] = T.loc[rows, :].div(row_sum, axis=0)
        
        # W_un: transpose of T_alpha_c
        W_un = T_alpha_c.T.copy()
        
        # Td: aggregate T to criteria level
        Td = pd.DataFrame(0.0, index=crits, columns=crits)
        
        for a in crits:
            rows = subcriteria.loc[
                subcriteria['criterion_id'] == a, 'sub_id'
            ].tolist()
            
            for b in crits:
                cols = subcriteria.loc[
                    subcriteria['criterion_id'] == b, 'sub_id'
                ].tolist()
                
                if rows and cols:
                    Td.at[a, b] = float(T.loc[rows, cols].mean().mean())
        
        # T_alpha_d: normalize Td by rows
        row_sum = Td.sum(axis=1).replace(0, 1.0)
        T_alpha_d = Td.div(row_sum, axis=0)
        
        # W_alpha: adjust W_un by criteria influences
        W_alpha = W_un.copy()
        sub_to_crit = dict(zip(subcriteria['sub_id'], subcriteria['criterion_id']))
        
        for col in W_alpha.columns:
            cj = sub_to_crit.get(col)
            if cj is None:
                continue
            
            for ci in crits:
                rows = subcriteria.loc[
                    subcriteria['criterion_id'] == ci, 'sub_id'
                ].tolist()
                
                if rows:
                    W_alpha.loc[rows, col] = W_alpha.loc[rows, col] * T_alpha_d.at[ci, cj]
        
        # Normalize W_alpha by columns
        col_sum = W_alpha.sum(axis=0).replace(0, np.nan)
        W_alpha = W_alpha.divide(col_sum, axis=1).fillna(0.0)
        
        # W_limit: power method to find limiting weights
        M = W_alpha.values.copy()
        
        for iteration in range(120):
            M2 = M @ M
            
            if np.max(np.abs(M2 - M)) < 1e-12:
                M = M2
                break
            
            M = M2
        
        W_limit = pd.DataFrame(M, index=W_alpha.index, columns=W_alpha.columns)
        
        # Global weights: average of rows in W_limit
        gw = W_limit.mean(axis=1)
        
        # Normalize to sum to 1
        gw_sum = gw.sum()
        if gw_sum > 0:
            gw = gw / gw_sum
        
        return {
            'T_alpha_c': T_alpha_c,
            'W_un': W_un,
            'Td': Td,
            'T_alpha_d': T_alpha_d,
            'W_alpha': W_alpha,
            'W_limit': W_limit,
            'gw': gw
        }
    
    except Exception as e:
        print(f"Error in danp_from_T: {e}")
        return empty_result


def supplier_scores(ratings: pd.DataFrame, respondents: pd.DataFrame,
                   gw: pd.Series, suppliers: pd.DataFrame,
                   filters: Optional[Dict] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate supplier scores based on ratings and DANP weights
    
    Returns:
        Tuple of (ranking DataFrame, aggregated ratings DataFrame)
    """
    if ratings is None or ratings.empty:
        empty_ranking = pd.DataFrame(columns=['supplier_id', 'score'])
        return empty_ranking, pd.DataFrame()
    
    if respondents is None or respondents.empty:
        empty_ranking = pd.DataFrame(columns=['supplier_id', 'score'])
        return empty_ranking, pd.DataFrame()
    
    if gw is None or gw.empty:
        empty_ranking = pd.DataFrame(columns=['supplier_id', 'score'])
        return empty_ranking, pd.DataFrame()
    
    try:
        # Get respondent weights
        rw = respondents.set_index('respondent_id')['weight'].astype(float)
        if not np.isfinite(rw).all() or rw.sum() <= 0:
            rw = pd.Series(1.0, index=respondents['respondent_id'])   # fallback bobot sama rata
        rw = rw / rw.sum()

        
        # Copy ratings
        r = ratings.copy()
        
        # Apply filters
        if filters:
            for k, v in filters.items():
                if v and v != 'ALL' and k in r.columns:
                    r = r[r[k] == v]
        
        # Check if any ratings remain after filtering
        if len(r) == 0:
            if suppliers is not None and not suppliers.empty:
                return suppliers.assign(score=0.0)[['supplier_id', 'score']], pd.DataFrame()
            return pd.DataFrame(columns=['supplier_id', 'score']), pd.DataFrame()
        
        # Clip ratings to valid range
        r['rating'] = r['rating'].clip(1, 5)
        
        # Merge with respondent weights
        r = r.merge(
            rw.rename('r_weight'),
            left_on='respondent_id',
            right_index=True,
            how='left'
        )
        
        # Calculate weighted ratings
        r['weighted'] = r['rating'] * r['r_weight']
        
        # Aggregate by supplier and subcriteria
        agg = r.groupby(['supplier_id', 'sub_id'])['weighted'].sum().unstack(fill_value=0)
        
        # Normalize to 0-1 scale (ratings are 1-5)
        agg = agg / 5.0
        
        # Reindex to match global weights
        agg = agg.reindex(columns=gw.index, fill_value=0)
        
        # Calculate scores
        scores = agg.mul(gw, axis=1).sum(axis=1).sort_values(ascending=False)
        
        # Build ranking DataFrame
        ranking = scores.to_frame('score')
        
        if suppliers is not None and not suppliers.empty:
            ranking = ranking.merge(
                suppliers,
                left_index=True,
                right_on='supplier_id',
                how='left'
            )
        else:
            ranking = ranking.reset_index()
            ranking.columns = ['supplier_id', 'score']
        
        return ranking, agg
    
    except Exception as e:
        print(f"Error in supplier_scores: {e}")
        empty_ranking = pd.DataFrame(columns=['supplier_id', 'score'])
        return empty_ranking, pd.DataFrame()