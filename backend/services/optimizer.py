from typing import Dict, List


def rank_phages(scores: Dict[str, float]) -> List[Dict[str, object]]:
    """
    Rank phages from highest to lowest predicted compatibility score.
    """
    ranked = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return [
        {
            "phage": phage,
            "score": round(float(score), 4),
            "rank": rank,
        }
        for rank, (phage, score) in enumerate(ranked, start=1)
    ]


def select_cocktail(
    ranked_phages: List[Dict[str, object]],
    size: int = 3,
) -> List[str]:
    """
    Select the highest-ranked phages for the initial MVP cocktail.
    """
    if size < 1:
        raise ValueError("Cocktail size must be at least 1.")

    return [
        str(candidate["phage"])
        for candidate in ranked_phages[:size]
    ]
