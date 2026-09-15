import json
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PHAGE_EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "phage_embeddings"
BACTERIAL_DATA_DIR = PROJECT_ROOT / "data" / "bacterial_data"


def load_embedding_file(path: Path) -> List[float]:
    """
    Load a precomputed embedding from a JSON file.

    Expected JSON format:
        [0.123, 0.456, 0.789, ...]
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Embedding file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        embedding = json.load(file)

    if not isinstance(embedding, list):
        raise ValueError(
            f"Embedding file must contain a JSON list: {path}"
        )

    if not embedding:
        raise ValueError(
            f"Embedding file is empty: {path}"
        )

    if not all(isinstance(value, (int, float)) for value in embedding):
        raise ValueError(
            f"Embedding must contain only numbers: {path}"
        )

    return [float(value) for value in embedding]


def load_bacterial_embedding(
    bacterium_id: str,
) -> List[float]:
    """
    Load the precomputed ESM-2 embedding for a bacterium.

    Expected file:
        data/bacterial_data/<bacterium_id>.json
    """

    path = BACTERIAL_DATA_DIR / f"{bacterium_id}.json"

    return load_embedding_file(path)
import json
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PHAGE_EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "phage_embeddings"
BACTERIAL_DATA_DIR = PROJECT_ROOT / "data" / "bacterial_data"


def load_embedding_file(path: Path) -> List[float]:
    """
    Load a precomputed embedding from a JSON file.

    Expected JSON format:
        [0.123, 0.456, 0.789, ...]
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Embedding file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        embedding = json.load(file)

    if not isinstance(embedding, list):
        raise ValueError(
            f"Embedding file must contain a JSON list: {path}"
        )

    if not embedding:
        raise ValueError(
            f"Embedding file is empty: {path}"
        )

    if not all(isinstance(value, (int, float)) for value in embedding):
        raise ValueError(
            f"Embedding must contain only numbers: {path}"
        )

    return [float(value) for value in embedding]


def load_bacterial_embedding(
    bacterium_id: str,
) -> List[float]:
    """
    Load the precomputed ESM-2 embedding for a bacterium.

    Expected file:
        data/bacterial_data/<bacterium_id>.json
    """

    path = BACTERIAL_DATA_DIR / f"{bacterium_id}.json"

    return load_embedding_file(path)

import json
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PHAGE_EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "phage_embeddings"
BACTERIAL_DATA_DIR = PROJECT_ROOT / "data" / "bacterial_data"


def load_embedding_file(path: Path) -> List[float]:
    """
    Load a precomputed embedding from a JSON file.

    Expected JSON format:
        [0.123, 0.456, 0.789, ...]
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Embedding file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        embedding = json.load(file)

    if not isinstance(embedding, list):
        raise ValueError(
            f"Embedding file must contain a JSON list: {path}"
        )

    if not embedding:
        raise ValueError(
            f"Embedding file is empty: {path}"
        )

    if not all(isinstance(value, (int, float)) for value in embedding):
        raise ValueError(
            f"Embedding must contain only numbers: {path}"
        )

    return [float(value) for value in embedding]


def load_bacterial_embedding(
    bacterium_id: str,
) -> List[float]:
    """
    Load the precomputed ESM-2 embedding for a bacterium.

    Expected file:
        data/bacterial_data/<bacterium_id>.json
    """

    path = BACTERIAL_DATA_DIR / f"{bacterium_id}.json"

    return load_embedding_file(path)


def load_phage_embeddings() -> Dict[str, List[float]]:
    """
    Load all available precomputed phage RBP embeddings.

    Expected files:
        data/phage_embeddings/<phage_id>.json

    Returns:
        {
            "phage_001": [0.1, 0.2, ...],
            "phage_002": [0.3, 0.4, ...]
        }
    """

    if not PHAGE_EMBEDDINGS_DIR.exists():
        raise FileNotFoundError(
            f"Phage embedding directory not found: "
            f"{PHAGE_EMBEDDINGS_DIR}"
        )

    embeddings: Dict[str, List[float]] = {}

    for path in sorted(PHAGE_EMBEDDINGS_DIR.glob("*.json")):
        phage_id = path.stem
        embeddings[phage_id] = load_embedding_file(path)

    if not embeddings:
        raise ValueError(
            f"No phage embedding files found in "
            f"{PHAGE_EMBEDDINGS_DIR}"
        )

    return embeddings
