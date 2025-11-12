
import pandas as pd, numpy as np

def safe_reindex(df: pd.DataFrame, index=None, columns=None, fill=0):
    if index is not None and not isinstance(index, pd.Index):
        index = pd.Index(index)
    if columns is not None and not isinstance(columns, pd.Index):
        columns = pd.Index(columns)
    # If df is empty, build from scratch
    if df is None or df.empty:
        return pd.DataFrame(fill, index=index if index is not None else [], columns=columns if columns is not None else [])
    # Reindex with fill
    out = df.copy()
    if index is not None:
        out = out.reindex(index=index, fill_value=fill)
    if columns is not None:
        out = out.reindex(columns=columns, fill_value=fill)
    return out

def is_empty_df(df):
    return (df is None) or (isinstance(df, pd.DataFrame) and (df.shape[0]==0 or df.shape[1]==0))

def is_empty_series(s):
    return (s is None) or (isinstance(s, pd.Series) and (s.size==0))

def safe_series(values=None, index=None, name=None, fill=0.0):
    if values is None or (hasattr(values, '__len__') and len(values)==0):
        return pd.Series([], index=pd.Index([], name=None), dtype=float, name=name)
    return pd.Series(values, index=index, name=name, dtype=float)
