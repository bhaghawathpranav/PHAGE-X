from app.research_model import get_research_model
import numpy as np


def test_research_artifact_is_blocked_from_release():
    status = get_research_model().status()
    assert status["release_approved"] is False
    assert status["benchmark_hosts"] > 0
    assert status["candidate_phages"] == 105
    assert status["model"] == "xgboost.XGBClassifier"
    assert status["decision_threshold"] == status["test_metrics"]["decision_threshold"]


def test_held_out_host_ranking_uses_real_embeddings_and_blocks_cocktail():
    model = get_research_model()
    host_id = str(model.host_ids[0])
    result = model.rank(host_id, 10)
    assert result.split_role == "held-out-test-host"
    assert result.feature_source.startswith("PhageHostLearn")
    assert result.cocktail_status == "blocked"
    assert len(result.candidates) == 10
    assert all(
        result.candidates[index].compatibility >= result.candidates[index + 1].compatibility
        for index in range(9)
    )
    assert all(item.safety_status.startswith("blocked") for item in result.candidates)
    assert all(
        item.decision == (
            "higher-priority-research-signal"
            if item.compatibility >= model.decision_threshold
            else "lower-priority-research-signal"
        )
        for item in result.candidates
    )


def test_novel_vector_path_uses_same_real_phage_catalog():
    model = get_research_model()
    vector = model.host_vectors[0].copy()
    distribution = model.distribution_check(vector)
    candidates = model.rank_vector(vector, 7)
    assert distribution["status"] == "within-runtime-reference-envelope"
    assert distribution["nearest_reference_cosine"] > 0.999
    assert len(candidates) == 7
    assert all(candidate.rationale for candidate in candidates)
    assert all(candidate.safety_status.startswith("blocked") for candidate in candidates)


def test_out_of_distribution_vector_is_rejected():
    model = get_research_model()
    with np.testing.assert_raises_regex(ValueError, "outside"):
        model.rank_vector(np.zeros(1280, dtype=np.float32), 5)


def test_xgboost_scores_vary_by_candidate_and_host():
    model = get_research_model()
    first = model.rank(str(model.host_ids[0]), 10)
    second = model.rank(str(model.host_ids[1]), 10)
    first_scores = [item.compatibility for item in first.candidates]
    second_scores = [item.compatibility for item in second.candidates]
    assert len(set(first_scores)) > 1
    assert first_scores != second_scores
