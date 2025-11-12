import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List

# Required files and their minimal columns
REQUIRED_FILES = {
    'hor_events.csv': ['event_id', 'name', 'severity'],
    'hor_agents.csv': ['agent_id', 'name', 'occurrence'],
    'hor_R.csv': [],  # Matrix file
    'hor_actions.csv': ['action_id', 'name', 'difficulty', 'cost', 'manhours'],
    'hor_effectiveness.csv': [],  # Matrix file
    'respondents.csv': ['respondent_id', 'name', 'weight'],
    'criteria.csv': ['criterion_id', 'name'],
    'subcriteria.csv': ['sub_id', 'name', 'criterion_id'],
    'dematel_edges.csv': ['respondent_id', 'from_sub', 'to_sub', 'score'],
    'suppliers.csv': ['supplier_id', 'name', 'region'],
    'supplier_ratings.csv': ['supplier_id', 'sub_id', 'respondent_id', 'rating']
}


def ensure_minimal_templates(tpl_dir: Path):
    """
    Ensure all required template files exist with minimal data
    """
    tpl_dir.mkdir(parents=True, exist_ok=True)
    
    # HOR Events
    p = tpl_dir / 'hor_events.csv'
    if not p.exists():
        pd.DataFrame({
            'event_id': ['E1', 'E2', 'E3'],
            'name': ['Risk Event 1', 'Risk Event 2', 'Risk Event 3'],
            'description': ['Description 1', 'Description 2', 'Description 3'],
            'severity': [7, 5, 8]
        }).to_csv(p, index=False)
    
    # HOR Agents
    p = tpl_dir / 'hor_agents.csv'
    if not p.exists():
        pd.DataFrame({
            'agent_id': ['A1', 'A2', 'A3'],
            'name': ['Agent 1', 'Agent 2', 'Agent 3'],
            'occurrence': [6, 7, 5]
        }).to_csv(p, index=False)
    
    # HOR R Matrix
    p = tpl_dir / 'hor_R.csv'
    if not p.exists():
        pd.DataFrame(
            [[2, 1, 0], [1, 3, 2], [0, 2, 1]],
            index=['E1', 'E2', 'E3'],
            columns=['A1', 'A2', 'A3']
        ).to_csv(p)
    
    # HOR Actions
    p = tpl_dir / 'hor_actions.csv'
    if not p.exists():
        pd.DataFrame({
            'action_id': ['M1', 'M2', 'M3'],
            'name': ['Mitigation 1', 'Mitigation 2', 'Mitigation 3'],
            'difficulty': [3, 2, 4],
            'cost': [100, 150, 80],
            'manhours': [40, 60, 35]
        }).to_csv(p, index=False)
    
    # HOR Effectiveness Matrix
    p = tpl_dir / 'hor_effectiveness.csv'
    if not p.exists():
        pd.DataFrame(
            [[0.8, 0.5, 0.3], [0.6, 0.9, 0.4], [0.4, 0.7, 0.8]],
            index=['A1', 'A2', 'A3'],
            columns=['M1', 'M2', 'M3']
        ).to_csv(p)
    
    # Respondents
    p = tpl_dir / 'respondents.csv'
    if not p.exists():
        pd.DataFrame({
            'respondent_id': ['R1', 'R2', 'R3'],
            'name': ['Expert 1', 'Expert 2', 'Expert 3'],
            'role': ['Manager', 'Analyst', 'Director'],
            'weight': [1.0, 0.8, 1.2]
        }).to_csv(p, index=False)
    
    # Criteria
    p = tpl_dir / 'criteria.csv'
    if not p.exists():
        pd.DataFrame({
            'criterion_id': ['C1', 'C2', 'C3'],
            'name': ['Quality', 'Cost', 'Delivery']
        }).to_csv(p, index=False)
    
    # Subcriteria
    p = tpl_dir / 'subcriteria.csv'
    if not p.exists():
        pd.DataFrame({
            'sub_id': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'],
            'name': ['Quality-A', 'Quality-B', 'Cost-A', 'Cost-B', 'Delivery-A', 'Delivery-B'],
            'criterion_id': ['C1', 'C1', 'C2', 'C2', 'C3', 'C3']
        }).to_csv(p, index=False)
    
    # DEMATEL Edges
    p = tpl_dir / 'dematel_edges.csv'
    if not p.exists():
        edges = []
        subs = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']
        resp = ['R1', 'R2', 'R3']
        
        for r in resp:
            for i, s1 in enumerate(subs):
                for j, s2 in enumerate(subs):
                    if i != j:  # No self-influence
                        edges.append({
                            'respondent_id': r,
                            'from_sub': s1,
                            'to_sub': s2,
                            'score': np.random.randint(0, 5)
                        })
        
        pd.DataFrame(edges).to_csv(p, index=False)
    
    # Suppliers
    p = tpl_dir / 'suppliers.csv'
    if not p.exists():
        pd.DataFrame({
            'supplier_id': ['SUP1', 'SUP2', 'SUP3', 'SUP4'],
            'name': ['Supplier A', 'Supplier B', 'Supplier C', 'Supplier D'],
            'region': ['North', 'South', 'East', 'West']
        }).to_csv(p, index=False)
    
    # Supplier Ratings
    p = tpl_dir / 'supplier_ratings.csv'
    if not p.exists():
        ratings = []
        sups = ['SUP1', 'SUP2', 'SUP3', 'SUP4']
        subs = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']
        resp = ['R1', 'R2', 'R3']
        
        for sup in sups:
            for sub in subs:
                for r in resp:
                    ratings.append({
                        'supplier_id': sup,
                        'sub_id': sub,
                        'respondent_id': r,
                        'rating': np.random.randint(3, 6),
                        'plant_id': 'P1',
                        'time_period': '2024-Q1',
                        'cheese_type': 'Mozzarella'
                    })
        
        pd.DataFrame(ratings).to_csv(p, index=False)
    
    # Allocation files
    p = tpl_dir / 'allocation_plants.csv'
    if not p.exists():
        pd.DataFrame({
            'plant_id': ['PlantA', 'PlantB'],
            'demand': [100, 120]
        }).to_csv(p, index=False)
    
    p = tpl_dir / 'allocation_suppliers.csv'
    if not p.exists():
        pd.DataFrame({
            'supplier_id': ['SUP1', 'SUP2', 'SUP3', 'SUP4'],
            'capacity': [150, 120, 90, 80],
            'unit_cost': [4.5, 4.2, 4.0, 4.1],
            'emission_score': [0.6, 0.8, 1.0, 0.7]
        }).to_csv(p, index=False)


def preflight_report(tpl_dir: Path) -> pd.DataFrame:
    """
    Generate a preflight report checking all required files
    
    Returns:
        DataFrame with columns: file, status, rows, cols, issues
    """
    report = []
    
    for filename, required_cols in REQUIRED_FILES.items():
        filepath = tpl_dir / filename
        
        if not filepath.exists():
            report.append({
                'file': filename,
                'status': 'MISSING',
                'rows': 0,
                'cols': 0,
                'issues': 'File does not exist'
            })
            continue
        
        try:
            # Read file
            if filename.endswith('_R.csv') or filename.endswith('_effectiveness.csv'):
                df = pd.read_csv(filepath, index_col=0)
            else:
                df = pd.read_csv(filepath)
            
            # Check if empty
            if df.empty:
                report.append({
                    'file': filename,
                    'status': 'EMPTY',
                    'rows': 0,
                    'cols': len(df.columns),
                    'issues': 'File is empty'
                })
                continue
            
            # Check required columns (skip for matrix files)
            issues = []
            if required_cols:
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    issues.append(f"Missing columns: {', '.join(missing_cols)}")
            
            # Check for duplicates in ID columns
            id_cols = [c for c in df.columns if c.endswith('_id')]
            for col in id_cols:
                if df[col].duplicated().any():
                    dup_count = df[col].duplicated().sum()
                    issues.append(f"Duplicate {col}: {dup_count} rows")
            
            # Determine status
            if issues:
                status = 'WARNING'
            else:
                status = 'OK'
            
            report.append({
                'file': filename,
                'status': status,
                'rows': len(df),
                'cols': len(df.columns),
                'issues': '; '.join(issues) if issues else 'None'
            })
        
        except Exception as e:
            report.append({
                'file': filename,
                'status': 'ERROR',
                'rows': 0,
                'cols': 0,
                'issues': str(e)
            })
    
    return pd.DataFrame(report)


def check_data_integrity(tpl_dir: Path) -> Dict[str, List[str]]:
    """
    Perform deeper data integrity checks
    
    Returns:
        Dict of {check_name: [list of issues]}
    """
    issues = {}
    
    try:
        # Load all data
        events = pd.read_csv(tpl_dir / 'hor_events.csv')
        agents = pd.read_csv(tpl_dir / 'hor_agents.csv')
        R = pd.read_csv(tpl_dir / 'hor_R.csv', index_col=0)
        actions = pd.read_csv(tpl_dir / 'hor_actions.csv')
        E = pd.read_csv(tpl_dir / 'hor_effectiveness.csv', index_col=0)
        respondents = pd.read_csv(tpl_dir / 'respondents.csv')
        criteria = pd.read_csv(tpl_dir / 'criteria.csv')
        subcriteria = pd.read_csv(tpl_dir / 'subcriteria.csv')
        edges = pd.read_csv(tpl_dir / 'dematel_edges.csv')
        suppliers = pd.read_csv(tpl_dir / 'suppliers.csv')
        ratings = pd.read_csv(tpl_dir / 'supplier_ratings.csv')
        
        # Check R matrix alignment
        missing_events = [e for e in R.index if e not in events['event_id'].values]
        missing_agents = [a for a in R.columns if a not in agents['agent_id'].values]
        
        if missing_events:
            issues['R Matrix'] = [f"Events not in hor_events.csv: {missing_events}"]
        if missing_agents:
            issues.setdefault('R Matrix', []).append(f"Agents not in hor_agents.csv: {missing_agents}")
        
        # Check E matrix alignment
        missing_agents_e = [a for a in E.index if a not in agents['agent_id'].values]
        missing_actions = [m for m in E.columns if m not in actions['action_id'].values]
        
        if missing_agents_e:
            issues['E Matrix'] = [f"Agents not in hor_agents.csv: {missing_agents_e}"]
        if missing_actions:
            issues.setdefault('E Matrix', []).append(f"Actions not in hor_actions.csv: {missing_actions}")
        
        # Check subcriteria references
        invalid_crits = subcriteria[~subcriteria['criterion_id'].isin(criteria['criterion_id'])]
        if not invalid_crits.empty:
            issues['Subcriteria'] = [f"Invalid criterion_id: {invalid_crits['criterion_id'].unique().tolist()}"]
        
        # Check edges references
        invalid_resp = edges[~edges['respondent_id'].isin(respondents['respondent_id'])]
        invalid_from = edges[~edges['from_sub'].isin(subcriteria['sub_id'])]
        invalid_to = edges[~edges['to_sub'].isin(subcriteria['sub_id'])]
        
        if not invalid_resp.empty:
            issues['DEMATEL Edges'] = [f"Invalid respondent_id: {len(invalid_resp)} rows"]
        if not invalid_from.empty:
            issues.setdefault('DEMATEL Edges', []).append(f"Invalid from_sub: {len(invalid_from)} rows")
        if not invalid_to.empty:
            issues.setdefault('DEMATEL Edges', []).append(f"Invalid to_sub: {len(invalid_to)} rows")
        
        # Check ratings references
        invalid_sup = ratings[~ratings['supplier_id'].isin(suppliers['supplier_id'])]
        invalid_sub = ratings[~ratings['sub_id'].isin(subcriteria['sub_id'])]
        invalid_resp_r = ratings[~ratings['respondent_id'].isin(respondents['respondent_id'])]
        
        if not invalid_sup.empty:
            issues['Supplier Ratings'] = [f"Invalid supplier_id: {len(invalid_sup)} rows"]
        if not invalid_sub.empty:
            issues.setdefault('Supplier Ratings', []).append(f"Invalid sub_id: {len(invalid_sub)} rows")
        if not invalid_resp_r.empty:
            issues.setdefault('Supplier Ratings', []).append(f"Invalid respondent_id: {len(invalid_resp_r)} rows")
        
        # Value range checks
        bad_severity = events[~events['severity'].between(1, 10)]
        if not bad_severity.empty:
            issues['Value Ranges'] = [f"Severity out of range [1-10]: {len(bad_severity)} rows"]
        
        bad_occurrence = agents[~agents['occurrence'].between(1, 10)]
        if not bad_occurrence.empty:
            issues.setdefault('Value Ranges', []).append(f"Occurrence out of range [1-10]: {len(bad_occurrence)} rows")
        
        bad_rating = ratings[~ratings['rating'].between(1, 5)]
        if not bad_rating.empty:
            issues.setdefault('Value Ranges', []).append(f"Rating out of range [1-5]: {len(bad_rating)} rows")
        
    except Exception as e:
        issues['System Error'] = [str(e)]
    
    return issues