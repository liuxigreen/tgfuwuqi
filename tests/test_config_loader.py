from trade_core.config import load_config


def test_nested_config_values_loaded():
    cfg = load_config()
    assert cfg["latency_structured"]["fast_path"]["target_total_ms"] == 4000
    assert cfg["daily_limits"]["max_daily_loss_pct"] == 2.0
    assert cfg["cache"]["ttl_sentiment"] == 60
    assert cfg["exit_rules"]["first_tp_pct"] > 0
    assert "okx-cex-market" in cfg["skill_registry"]["skills"]
