# Data Contracts (Core Schemas)

> Canonical protocol is structured JSON (dataclass/pydantic compatible). No natural-language execution protocol.

## 1. RadarSignal
- `signal_id: str`
- `source: str` (radar name)
- `symbol: str`
- `market_type: str` (`spot|swap|futures`)
- `direction_hint: str` (`long|short|neutral|unknown`)
- `strength: float|None`
- `features: dict`
- `detected_at: datetime`
- `ttl_seconds: int`

## 2. MarketSnapshot
- `symbol, market_type, price, bid, ask, spread_bps`
- `volume_24h, volatility, timestamp, source, is_mock`

## 3. SentimentSnapshot
- `symbol, sentiment_score(-1..1), trend, confidence, timestamp, source, is_mock`

## 4. SmartMoneySnapshot
- `symbol, long_short_ratio, capital_weighted_direction, avg_win_rate, trader_count, confidence, timestamp, source, is_mock`

## 5. AccountSnapshot
- `equity_total, equity_available, exposure_pct, open_positions_count`
- `daily_pnl_pct|None, daily_pnl_usdt|None`
- `timestamp, source, is_mock, warning|None`

## 6. NuwaEval
- `nuwa_version, market_regime, signal_quality, continuation_probability`
- `manipulation_risk, thesis_status, preferred_action, preferred_exit_style`
- `block_trade: bool, confidence, reason_codes[], timestamp`

## 7. ScoreBreakdown
- component scores (`market, oi, funding, sentiment, smart_money, nuwa`)
- `risk_penalty, total_score`
- `missing_inputs[]`
- `warnings[]`

## 8. TradeDecision
- `decision_id, pipeline_id, symbol, market_type`
- `direction, action` (`observe|propose|demo_auto|blocked|open|exit`)
- `mode`
- `confidence, final_score`
- `risk_status` (`ok|blocked|review_required`)
- `reason_codes[], blocked_reasons[], warnings[]`

## 9. ExitPolicy
- `exit_policy_id`
- `stop_loss_pct` (required for open)
- `first_take_profit_pct` (required for open)
- `final_take_profit_pct` (required for open)
- `partial_take_profit_pct` (required for open)
- `trailing_stop` (optional struct)
- `time_stop_minutes`
- `thesis_invalidation_rules[]`

## 10. OrderIntent
- `intent_id, decision_id, symbol, market_type`
- `side` (`buy|sell|none`)
- `entry_type, size_mode, size`
- `dry_run: bool`
- `mode`
- `exit_policy_id`
- exit fields mirrored (stop/tp/partial/trailing/time)
- `risk_summary`
- `reason_codes[]`

## 11. ExecutionResult
- `executed: bool, blocked: bool, dry_run: bool`
- `backend, profile`
- `returncode|None, error_code|None`
- `stdout_summary, stderr_summary`
- `timestamp`

## 12. PositionState
- `position_id, symbol, side, size, avg_entry`
- `unrealized_pnl, leverage, margin_mode`
- `opened_at, updated_at`
- `linked_exit_policy_id`

## 13. PositionExitEvaluation
- `position_id, action` (`HOLD|REDUCE|TIGHTEN_STOP|TAKE_PARTIAL_PROFIT|EXIT_FULL|BLOCK_ADD|REVIEW_REQUIRED`)
- `trigger_reasons[]`
- `risk_flags[]`
- `recommended_updates` (e.g. stop tightening)

## 14. DecisionSnapshot
- `snapshot_id, decision_id, pipeline_id, timestamp`
- raw inputs (radar, market/account/sentiment/smartmoney, nuwa)
- `score_breakdown, risk_result, decision, order_intent, execution_result`
- `latency_ms, adapter_status, cache_status`
- `selected_skills[], selected_recipe`

## 15. OutcomeEvaluation
- `outcome_id, snapshot_id, evaluated_at`
- `horizon_minutes`
- `direction_correct|None`
- `realized_pnl_pct|None, realized_pnl_usdt|None`
- `max_drawdown_pct|None`
- `label` (`win|loss|inconclusive|unavailable`)
- `data_quality` (`ok|insufficient|unavailable`)

## 16. ExperienceRecord
- `experience_id, snapshot_id, outcome_id`
- `feature_fingerprint`
- `lessons[]`
- `confidence`
- `created_at`

## 17. ProposedChange
- `proposal_id, date`
- `changes[]` with `type,target,old_value,new_value,reason,evidence`
- `requires_human_approval: true`
- `safe_to_auto_apply: false`
- `forbidden_auto_changes[]`
