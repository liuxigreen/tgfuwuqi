from trade_core.models import Direction, MarketSnapshot, NuwaEval, RadarSignal, SentimentSnapshot, SmartMoneySnapshot
from trade_core.scoring import compute_score


def test_resonance_score_higher():
    radar = RadarSignal("BTC-USDT-SWAP", "swap", Direction.LONG, 80, "radar", "2026-04-28T00:00:00Z", {})
    nuwa = NuwaEval("nuwa-v1", "trend", "cont", 0.7, 0.8, 0.2, "small_probe", False, 0.8, "")
    market = MarketSnapshot("BTC-USDT-SWAP", 68000, 2.0, 10.0, 0.0002, 7.0, 0.6, 0.8, "2026-04-28T00:00:00Z")
    senti = SentimentSnapshot("BTC-USDT-SWAP", 0.7, "up", False, 0.1, "2026-04-28T00:00:00Z")
    smart = SmartMoneySnapshot("BTC-USDT-SWAP", Direction.LONG, Direction.LONG, 0.6, 1.2, "accumulate", 67000, 68000, 0.4, "2026-04-28T00:00:00Z")
    high = compute_score(radar, nuwa, market, senti, smart).total_score
    smart.weighted_direction = Direction.SHORT
    low = compute_score(radar, nuwa, market, senti, smart).total_score
    assert high > low
