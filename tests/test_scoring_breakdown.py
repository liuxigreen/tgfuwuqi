from trade_core.models import Direction, NuwaEval, RadarSignal
from trade_core.scoring import compute_score


def test_breakdown_fields_present():
    radar = RadarSignal("BTC-USDT", "spot", Direction.LONG, 70, "x", "2026-04-28T00:00:00Z", {})
    nuwa = NuwaEval("v1", "trend", "c", 0.7, 0.7, 0.2, "propose", False, 0.8, "")
    out = compute_score(radar, nuwa)
    assert hasattr(out, "market_score") and hasattr(out, "oi_score") and hasattr(out, "funding_score")


def test_missing_optional_adapters_no_crash():
    radar = RadarSignal("BTC-USDT", "spot", Direction.LONG, 70, "x", "2026-04-28T00:00:00Z", {})
    nuwa = NuwaEval("v1", "trend", "c", 0.7, 0.7, 0.2, "propose", False, 0.8, "")
    out = compute_score(radar, nuwa, None, None, None)
    assert out.total_score >= 0
