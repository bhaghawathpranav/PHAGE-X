import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List


DATA_PATH = Path(__file__).parent.parent / "data" / "demo_data.json"


@lru_cache(maxsize=1)
def load_demo_data() -> Dict[str, List[Dict[str, Any]]]:
    """Load immutable demo fixtures once per process instead of once per request."""
    with DATA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)
