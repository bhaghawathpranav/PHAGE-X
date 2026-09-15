from typing import Dict


def explain_candidate(
    phage_id: str,
    compatibility_score: float,
    rank: int,
) -> str:
    """
    Generate a simple explanation for a ranked phage candidate.
    """

    if compatibility_score >= 0.90:
        level = "Very high"
    elif compatibility_score >= 0.80:
        level = "High"
    elif compatibility_score >= 0.70:
        level = "Moderate"
    else:
        level = "Lower"

    return (
        f"{level} predicted compatibility "
        f"(score {compatibility_score:.2f}, rank {rank})."
    )


def explain_cocktail(
    cocktail_scores: Dict[str, float],
) -> str:
    """
    Explain the initial cocktail selection.
    """

    if not cocktail_scores:
        return "No phages were selected for the cocktail."

    best_phage = max(
        cocktail_scores,
        key=cocktail_scores.get,
    )

    return (
        f"{len(cocktail_scores)} phages selected, "
        f"with {best_phage} having the highest "
        f"predicted compatibility."
    )
