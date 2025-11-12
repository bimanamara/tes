
import pandas as pd, numpy as np

def auto_insights(weighted, ARP, detail, dem, danp, ranking, alloc):
    bullets = []

    # HOR
    try:
        if weighted is not None and not weighted.empty:
            top_event = weighted.sum(axis=1).sort_values(ascending=False).index[:1].tolist()
            bullets.append(f"HOR: Event dengan kontribusi terbesar pada S×R adalah {', '.join(top_event)}.")
        if ARP is not None and ARP.size>0:
            top_agent = ARP.sort_values(ascending=False).index[:3].tolist()
            bullets.append(f"HOR: Tiga agen risiko teratas menurut ARP: {', '.join(top_agent)}.")
    except Exception:
        pass

    # Mitigation
    try:
        if detail is not None and not detail.empty:
            a = detail.sort_values('ETD', ascending=False).head(3).index.tolist()
            bullets.append(f"Mitigation: Aksi dengan ETD tertinggi: {', '.join(a)}.")
    except Exception:
        pass

    # DEMATEL
    try:
        if dem and dem.get('r') is not None and dem.get('c') is not None and len(dem['r'])>0:
            rel = (dem['r'] - dem['c']).sort_values(ascending=False)
            cause = rel.head(3).index.tolist()
            effect = rel.tail(3).index.tolist()
            bullets.append(f"DEMATEL: Subkriteria paling sebagai 'penyebab': {', '.join(cause)}; paling 'akibat': {', '.join(effect)}.")
    except Exception:
        pass

    # DANP
    try:
        gw = danp.get('gw') if isinstance(danp, dict) else None
        if gw is not None and gw.size>0:
            topw = gw.sort_values(ascending=False).head(5)
            bullets.append(f"DANP: Bobot global tertinggi: {', '.join([f'{i} ({v:.3f})' for i,v in topw.items()])}.")
    except Exception:
        pass

    # Suppliers
    try:
        if ranking is not None and len(ranking)>0:
            top_supp = ranking.sort_values('score', ascending=False).head(5)['supplier_id'].tolist()
            bullets.append(f"Suppliers: Peringkat teratas: {', '.join(top_supp)}.")
    except Exception:
        pass

    # Allocation
    try:
        if alloc is not None and len(alloc)>0:
            rshare = alloc.groupby('region')['quantity'].sum()
            rshare = (rshare / alloc['quantity'].sum()).sort_values(ascending=False).head(3)
            bullets.append(f"Allocation: Distribusi pasokan terbesar berasal dari region: {', '.join([f'{i} ({v:.1%})' for i,v in rshare.items()])}.")
    except Exception:
        pass

    return bullets
