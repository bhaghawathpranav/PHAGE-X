from app.research_model import get_research_model


def test_research_artifact_is_blocked_from_release():
    status = get_research_model().status()
    assert status["release_approved"] is False
    assert status["benchmark_hosts"] > 0
    assert status["candidate_phages"] == 105


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
