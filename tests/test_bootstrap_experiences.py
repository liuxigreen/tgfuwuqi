from trade_core.learning_loop.bootstrap import bootstrap_experiences


def test_bootstrap_candidates_are_historical():
    out = bootstrap_experiences("examples/historical_bootstrap_sample.json")
    assert out["historical_simulation"] is True
    assert out["candidates"][0]["trusted"] is False
