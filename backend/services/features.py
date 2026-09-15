from typing import Dict, List, Sequence

from backend.services.genome import get_bacterium_id, parse_fasta


def build_feature_input(
    genome_fasta: str,
    bacterial_embedding: Sequence[float],
    phage_embeddings: Dict[str, Sequence[float]],
    bacterium_id: str | None = None,
) -> Dict[str, object]:
    """
    Build the feature structure expected by the ML prediction layer.

    ESM-2 embeddings are precomputed for the MVP and are supplied to this
    function rather than generated during an API request.
    """

    # Get the bacterium ID from the request or FASTA header.
    resolved_id = get_bacterium_id(
        genome_fasta,
        bacterium_id,
    )

    # Validate the genome before preparing ML inputs.
    parse_fasta(genome_fasta)

    if not bacterial_embedding:
        raise ValueError("Bacterial embedding is empty.")

    if not phage_embeddings:
        raise ValueError("No phage embeddings were provided.")

    phages: List[Dict[str, object]] = []

    for phage_id, rbp_embedding in phage_embeddings.items():

        if not phage_id.strip():
            raise ValueError("Phage ID cannot be empty.")

        if not rbp_embedding:
            raise ValueError(
                f"RBP embedding is empty for phage '{phage_id}'."
            )

        phages.append(
            {
                "phage_id": phage_id,
                "rbp_embedding": list(rbp_embedding),
            }
        )

    return {
        "bacterium_id": resolved_id,
        "bacterial_embedding": list(bacterial_embedding),
        "phages": phages,
    }
