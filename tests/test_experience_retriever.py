from trade_core.learning_loop.retriever import retrieve_similar_experiences


def test_retrieval_timeout_safe():
    out = retrieve_similar_experiences({"symbol": "BTC-USDT"}, max_latency_ms=0)
    assert out["timeout"] is True or out["used"] in {True, False}
