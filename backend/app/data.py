import json
from pathlib import Path
from typing import Any, Dict, List


DATA_PATH = Path(__file__).parent.parent / "data" / "demo_data.json"


def load_demo_data() -> Dict[str, List[Dict[str, Any]]]:
    with DATA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)

