from typing import Dict, List


def rank_phages(
    predictions: List[Dict[str, object]],
) -> List[Dict[str, object]]:
    """
    Rank phages from highest to lowest compatibility score.

    Expected input from the ML layer:
        [
            {
                "phage_id": "phage_001",
                "compatibility_score": 0.87
            }
        ]
    """

    ranked = sorted(
        predictions,
        key=lambda item: float(item["compatibility_score"]),
        reverse=True,
    )

    return [
        {
            "phage_id": str(candidate["phage_id"]),
            "compatibility_score": round(
                float(candidate["compatibility_score"]),
                4,
            ),
            "rank": rank,
        }
        for rank, candidate in enumerate(ranked, start=1)
    ]


def select_cocktail(
    ranked_phages: List[Dict[str, object]],
    size: int = 3,
) -> List[str]:
    """
    Select the highest-ranked phages for the MVP cocktail.

    The current MVP uses compatibility ranking only.
    Diversity/redundancy optimization can be added once real
    phage metadata or embeddings are available.
    """

    if size < 1:
        raise ValueError("Cocktail size must be at least 1.")

    return [
        str(candidate["phage_id"])
        for candidate in ranked_phages[:size]
    ]
