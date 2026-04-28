from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class OperatingMode(str, Enum):
    OBSERVE = "observe"
    PROPOSE = "propose"
    DEMO_AUTO = "demo_auto"
    LIVE_GUARDED = "live_guarded"


class TradeAction(str, Enum):
    OBSERVE = "observe"
    PROPOSE = "propose"
    SMALL_PROBE = "small_probe"
    OPEN_LONG = "open_long"
    OPEN_SHORT = "open_short"
    REDUCE = "reduce"
    CLOSE = "close"
    BLOCKED = "blocked"


class Direction(str, Enum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


@dataclass
class RadarSignal:
    symbol: str
    market_type: str
    direction: Direction
    score: float
    source: str
    timestamp: str
    features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NuwaEval:
    version: str
    market_regime: str
    signal_archetype: str
    signal_quality: float
    continuation_probability: float
    manipulation_risk: float
    preferred_action: str
    block_trade: bool
    confidence: float
    notes: str = ""


@dataclass
class MarketSnapshot:
    symbol: str
    price: float
    price_change_24h_pct: float
    volume_change_pct: float
    funding_rate: float
    open_interest_change_pct: float
    volatility_score: float
    liquidity_score: float
    timestamp: str


@dataclass
class SentimentSnapshot:
    symbol: str
    sentiment_score: float
    sentiment_trend: str
    abnormal_sentiment_shift: bool
    news_risk: float
    timestamp: str


@dataclass
class SmartMoneySnapshot:
    symbol: str
    consensus_direction: Direction
    weighted_direction: Direction
    avg_win_rate: float
    long_short_ratio: float
    smart_money_trend: str
    entry_vwap: float
    current_price: float
    premium_discount_pct: float
    timestamp: str


@dataclass
class AccountSnapshot:
    equity_usdt: float
    available_usdt: float
    daily_pnl_pct: float
    open_positions_count: int
    same_symbol_existing_position: bool
    total_exposure_pct: float
    max_position_exposure_pct: float
    timestamp: str


@dataclass
class TradeDecision:
    action: TradeAction
    symbol: str
    market_type: str
    direction: Direction
    decision_id: str
    final_score: float
    confidence: float
    risk_status: str
    reason_codes: List[str]
    blocked_reasons: List[str]
    warnings: List[str]
    score_breakdown: Dict[str, Any]
    recommended_size_pct: float
    recommended_leverage: float
    preferred_execution: str
    nuwa_version: str
    mode: OperatingMode


@dataclass
class OrderIntent:
    symbol: str
    side: str
    market_type: str
    size_mode: str
    size: float
    entry_type: str
    stop_loss_pct: Optional[float]
    take_profit_pct: Optional[float]
    use_oco: bool
    use_trailing_stop: bool
    dry_run: bool
    reason_codes: List[str]
    risk_summary: Dict[str, Any]
    nuwa_version: str
    decision_id: str
    exit_policy_id: Optional[str] = None
    first_take_profit_pct: Optional[float] = None
    final_take_profit_pct: Optional[float] = None
    partial_take_profit_pct: Optional[float] = None
    trailing_stop: Optional[Dict[str, Any]] = None
    time_stop_minutes: Optional[int] = None
    exit_reason_plan: Optional[List[str]] = None


@dataclass
class PositionState:
    position_id: str
    symbol: str
    side: Direction
    entry_price: float
    current_price: float
    unrealized_pnl_pct: float
    age_minutes: int
    entry_reason_codes: List[str]
    thesis: str
    stop_loss_pct: float
    take_profit_pct: float


@dataclass
class ExitDecision:
    action: str
    urgency: str
    reason_codes: List[str]
    thesis_status: str
    recommended_reduce_pct: float
    tighten_stop: bool


@dataclass
class PositionExitEvaluation:
    position_id: str
    symbol: str
    side: Direction
    entry_price: float
    current_price: float
    unrealized_pnl_pct: float
    rr_progress: float
    thesis_status: str
    continuation_probability: float
    smart_money_alignment: str
    sentiment_alignment: str
    oi_confirmation: str
    time_in_position_minutes: int
    recommended_action: str
    reason_codes: List[str]


@dataclass
class ReportResult:
    title: str
    markdown: str
    json: Dict[str, Any]
    severity: str
    generated_at: str


def model_to_dict(model: Any) -> Dict[str, Any]:
    data = asdict(model)
    for key, value in list(data.items()):
        if isinstance(value, Enum):
            data[key] = value.value
    return data


def enum_from_value(enum_cls: Any, value: Any, default: Any):
    try:
        return enum_cls(value)
    except Exception:
        return default
