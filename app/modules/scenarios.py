
import json, re
from pathlib import Path
from datetime import datetime

SCN_DIR = "scenarios"

def _slug(name):
    name = re.sub(r"[^a-zA-Z0-9\-\_]+", "_", name.strip())
    return name[:64] or datetime.now().strftime("%Y%m%d_%H%M%S")

def save_scenario(base_out: Path, name: str, payload: dict):
    d = base_out/SCN_DIR
    d.mkdir(parents=True, exist_ok=True)
    fn = f"{_slug(name)}.json"
    p = d/fn
    payload['_saved_at'] = datetime.now().isoformat(timespec='seconds')
    with open(p, "w") as f:
        json.dump(payload, f, indent=2)
    return str(p)

def list_scenarios(base_out: Path):
    d = base_out/SCN_DIR
    if not d.exists(): return []
    return [p for p in d.glob("*.json")]

def load_scenario(base_out: Path, name: str):
    d = base_out/SCN_DIR
    p = d/name if name.endswith(".json") else d/f"{name}.json"
    if not p.exists(): return None
    import json
    with open(p) as f:
        return json.load(f)

def delete_scenario(base_out: Path, name: str):
    d = base_out/SCN_DIR
    p = d/name if name.endswith(".json") else d/f"{name}.json"
    if p.exists(): p.unlink()
    return True
