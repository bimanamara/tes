import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict

np.random.seed(42)  # For reproducibility


def generate(tpl_dir: Path) -> Dict[str, int]:
    """
    Generate comprehensive dummy data for all CSV files
    
    Returns:
        Dict with statistics about generated data
    """
    tpl_dir.mkdir(parents=True, exist_ok=True)
    stats = {}
    
    # ========================================================================
    # HOR EVENTS
    # ========================================================================
    n_events = 10
    events = pd.DataFrame({
        'event_id': [f'E{i+1:02d}' for i in range(n_events)],
        'name': [f'Risk Event {i+1}' for i in range(n_events)],
        'description': [f'Description for risk event {i+1}' for i in range(n_events)],
        'severity': np.random.randint(3, 11, n_events)
    })
    events.to_csv(tpl_dir / 'hor_events.csv', index=False)
    stats['events'] = len(events)
    
    # ========================================================================
    # HOR AGENTS
    # ========================================================================
    n_agents = 8
    agents = pd.DataFrame({
        'agent_id': [f'A{i+1:02d}' for i in range(n_agents)],
        'name': [f'Risk Agent {i+1}' for i in range(n_agents)],
        'occurrence': np.random.randint(3, 11, n_agents)
    })
    agents.to_csv(tpl_dir / 'hor_agents.csv', index=False)
    stats['agents'] = len(agents)
    
    # ========================================================================
    # HOR R MATRIX (Events × Agents)
    # ========================================================================
    R = pd.DataFrame(
        np.random.choice([0, 1, 2, 3], size=(n_events, n_agents), p=[0.3, 0.3, 0.25, 0.15]),
        index=events['event_id'],
        columns=agents['agent_id']
    )
    R.to_csv(tpl_dir / 'hor_R.csv')
    stats['R_cells'] = R.size
    
    # ========================================================================
    # HOR ACTIONS
    # ========================================================================
    n_actions = 12
    actions = pd.DataFrame({
        'action_id': [f'M{i+1:02d}' for i in range(n_actions)],
        'name': [f'Mitigation Action {i+1}' for i in range(n_actions)],
        'difficulty': np.random.randint(1, 6, n_actions),
        'cost': np.random.randint(50, 500, n_actions),
        'manhours': np.random.randint(10, 100, n_actions)
    })
    actions.to_csv(tpl_dir / 'hor_actions.csv', index=False)
    stats['actions'] = len(actions)
    
    # ========================================================================
    # HOR EFFECTIVENESS MATRIX (Agents × Actions)
    # ========================================================================
    E = pd.DataFrame(
        np.random.uniform(0.1, 1.0, size=(n_agents, n_actions)),
        index=agents['agent_id'],
        columns=actions['action_id']
    ).round(2)
    E.to_csv(tpl_dir / 'hor_effectiveness.csv')
    stats['E_cells'] = E.size
    
    # ========================================================================
    # RESPONDENTS
    # ========================================================================
    n_respondents = 5
    respondents = pd.DataFrame({
        'respondent_id': [f'R{i+1}' for i in range(n_respondents)],
        'name': [f'Expert {i+1}' for i in range(n_respondents)],
        'role': np.random.choice(['Manager', 'Analyst', 'Director', 'Specialist'], n_respondents),
        'weight': np.random.uniform(0.8, 1.5, n_respondents).round(2)
    })
    respondents.to_csv(tpl_dir / 'respondents.csv', index=False)
    stats['respondents'] = len(respondents)
    
    # ========================================================================
    # CRITERIA
    # ========================================================================
    criteria_names = ['Quality', 'Cost', 'Delivery', 'Service', 'Sustainability']
    n_criteria = len(criteria_names)
    criteria = pd.DataFrame({
        'criterion_id': [f'C{i+1}' for i in range(n_criteria)],
        'name': criteria_names
    })
    criteria.to_csv(tpl_dir / 'criteria.csv', index=False)
    stats['criteria'] = len(criteria)
    
    # ========================================================================
    # SUBCRITERIA
    # ========================================================================
    subcriteria_list = []
    sub_counter = 1
    
    for crit_idx, crit_id in enumerate(criteria['criterion_id']):
        n_subs = np.random.randint(2, 5)  # 2-4 subcriteria per criterion
        
        for j in range(n_subs):
            subcriteria_list.append({
                'sub_id': f'S{sub_counter:02d}',
                'name': f'{criteria.loc[crit_idx, "name"]}-Sub{j+1}',
                'criterion_id': crit_id
            })
            sub_counter += 1
    
    subcriteria = pd.DataFrame(subcriteria_list)
    subcriteria.to_csv(tpl_dir / 'subcriteria.csv', index=False)
    stats['subcriteria'] = len(subcriteria)
    
    # ========================================================================
    # DEMATEL EDGES
    # ========================================================================
    edges_list = []
    subs = subcriteria['sub_id'].tolist()
    
    for resp_id in respondents['respondent_id']:
        for from_sub in subs:
            for to_sub in subs:
                if from_sub != to_sub:  # No self-influence
                    # 30% chance of no influence (score=0)
                    if np.random.random() < 0.3:
                        score = 0
                    else:
                        score = np.random.randint(1, 5)
                    
                    edges_list.append({
                        'respondent_id': resp_id,
                        'from_sub': from_sub,
                        'to_sub': to_sub,
                        'score': score
                    })
    
    edges = pd.DataFrame(edges_list)
    edges.to_csv(tpl_dir / 'dematel_edges.csv', index=False)
    stats['dematel_edges'] = len(edges)
    
    # ========================================================================
    # SUPPLIERS
    # ========================================================================
    n_suppliers = 15
    regions = ['North', 'South', 'East', 'West', 'Central']
    
    suppliers = pd.DataFrame({
        'supplier_id': [f'SUP{i+1:02d}' for i in range(n_suppliers)],
        'name': [f'Supplier {chr(65+i)}' for i in range(n_suppliers)],
        'region': np.random.choice(regions, n_suppliers)
    })
    suppliers.to_csv(tpl_dir / 'suppliers.csv', index=False)
    stats['suppliers'] = len(suppliers)
    
    # ========================================================================
    # SUPPLIER RATINGS
    # ========================================================================
    ratings_list = []
    plants = ['P1', 'P2', 'P3']
    periods = ['2024-Q1', '2024-Q2', '2024-Q3', '2024-Q4']
    cheese_types = ['Mozzarella', 'Cheddar', 'Parmesan', 'Gouda']
    
    for sup_id in suppliers['supplier_id']:
        for sub_id in subcriteria['sub_id']:
            for resp_id in respondents['respondent_id']:
                # Generate multiple ratings (different plants, periods, types)
                n_ratings = np.random.randint(1, 4)  # 1-3 ratings per combination
                
                for _ in range(n_ratings):
                    ratings_list.append({
                        'supplier_id': sup_id,
                        'sub_id': sub_id,
                        'respondent_id': resp_id,
                        'rating': np.random.randint(2, 6),  # 2-5 rating
                        'plant_id': np.random.choice(plants),
                        'time_period': np.random.choice(periods),
                        'cheese_type': np.random.choice(cheese_types)
                    })
    
    ratings = pd.DataFrame(ratings_list)
    ratings.to_csv(tpl_dir / 'supplier_ratings.csv', index=False)
    stats['supplier_ratings'] = len(ratings)
    
    # ========================================================================
    # ALLOCATION PLANTS
    # ========================================================================
    allocation_plants = pd.DataFrame({
        'plant_id': ['PlantA', 'PlantB', 'PlantC'],
        'demand': [150, 200, 180]
    })
    allocation_plants.to_csv(tpl_dir / 'allocation_plants.csv', index=False)
    stats['allocation_plants'] = len(allocation_plants)
    
    # ========================================================================
    # ALLOCATION SUPPLIERS (with capacity and costs)
    # ========================================================================
    allocation_suppliers = pd.DataFrame({
        'supplier_id': suppliers['supplier_id'].head(10).tolist(),  # Use first 10 suppliers
        'capacity': np.random.randint(80, 200, 10),
        'unit_cost': np.random.uniform(3.5, 5.5, 10).round(2),
        'emission_score': np.random.uniform(0.4, 1.2, 10).round(2)
    })
    allocation_suppliers.to_csv(tpl_dir / 'allocation_suppliers.csv', index=False)
    stats['allocation_suppliers'] = len(allocation_suppliers)
    
    return stats


def generate_large_scale(tpl_dir: Path, scale: str = 'medium') -> Dict[str, int]:
    """
    Generate large-scale dummy data for stress testing
    
    Args:
        scale: 'small' (current), 'medium' (3x), 'large' (10x), 'xlarge' (30x)
    
    Returns:
        Dict with statistics
    """
    scale_factors = {
        'small': 1,
        'medium': 3,
        'large': 10,
        'xlarge': 30
    }
    
    factor = scale_factors.get(scale, 1)
    
    # Adjust random seed for variety
    np.random.seed(42 + factor)
    
    tpl_dir.mkdir(parents=True, exist_ok=True)
    stats = {}
    
    # Scale parameters
    n_events = 10 * factor
    n_agents = 8 * factor
    n_actions = 12 * factor
    n_respondents = 5 * factor
    n_criteria = 5
    n_subs_per_crit = 4 * factor
    n_suppliers = 15 * factor
    
    # Generate events
    events = pd.DataFrame({
        'event_id': [f'E{i+1:04d}' for i in range(n_events)],
        'name': [f'Risk Event {i+1}' for i in range(n_events)],
        'description': [f'Risk description {i+1}' for i in range(n_events)],
        'severity': np.random.randint(3, 11, n_events)
    })
    events.to_csv(tpl_dir / 'hor_events.csv', index=False)
    stats['events'] = len(events)
    
    # Generate agents
    agents = pd.DataFrame({
        'agent_id': [f'A{i+1:04d}' for i in range(n_agents)],
        'name': [f'Risk Agent {i+1}' for i in range(n_agents)],
        'occurrence': np.random.randint(3, 11, n_agents)
    })
    agents.to_csv(tpl_dir / 'hor_agents.csv', index=False)
    stats['agents'] = len(agents)
    
    # Generate R matrix (sparse for large scale)
    R = pd.DataFrame(
        np.random.choice([0, 1, 2, 3], size=(n_events, n_agents), p=[0.5, 0.25, 0.15, 0.1]),
        index=events['event_id'],
        columns=agents['agent_id']
    )
    R.to_csv(tpl_dir / 'hor_R.csv')
    stats['R_cells'] = R.size
    
    # Generate actions
    actions = pd.DataFrame({
        'action_id': [f'M{i+1:04d}' for i in range(n_actions)],
        'name': [f'Mitigation {i+1}' for i in range(n_actions)],
        'difficulty': np.random.randint(1, 6, n_actions),
        'cost': np.random.randint(50, 500, n_actions),
        'manhours': np.random.randint(10, 100, n_actions)
    })
    actions.to_csv(tpl_dir / 'hor_actions.csv', index=False)
    stats['actions'] = len(actions)
    
    # Generate E matrix (sparse)
    E = pd.DataFrame(
        np.where(np.random.random((n_agents, n_actions)) < 0.7,
                np.random.uniform(0.1, 1.0, (n_agents, n_actions)), 0),
        index=agents['agent_id'],
        columns=actions['action_id']
    ).round(2)
    E.to_csv(tpl_dir / 'hor_effectiveness.csv')
    stats['E_cells'] = E.size
    
    # Continue with other files...
    # (Similar scaling for remaining files)
    
    stats['scale'] = scale
    stats['factor'] = factor
    
    return stats