# Crypto Futures Bot Strategy Analysis — Round 1

> **Objective:** Identify 3-5 stable, reproducible strategy patterns from 30 AI trading bots on Moss.site platform.
> **Context:** USDT-M futures, 125-200x leverage, simulated PnL. Focus on STRATEGY PATTERNS, not absolute returns.
> **Stability Criteria:** Low liquidations, clear rules, risk management, viability with real capital.

---

## Methodology

Bots were evaluated against four stability criteria:

1. **Low liquidation count** relative to PnL generated
2. **Clear entry/exit rules** (not vague "all-in" directives)
3. **Defined risk management** (stop-loss, trailing stops, position sizing rules)
4. **Real-capital viability** (could survive outside simulated extreme conditions)

Bots were ranked by explicitness of parameters, risk controls present, and absence of pure gambling behavior.

---

## Pattern 1: Doomsday Sprint — Momentum Trend-Following with Rolling Compounds

**Representative Bots:** Doomsday Sprint, Newbie Bear Escape, Newbie Trend Escape v2, Roco Kingdom

### Core Parameters

| Parameter | Value |
|-----------|-------|
| **Leverage** | 150x (fixed) |
| **Direction bias** | Long 0.85 (strong bullish bias) |
| **Entry threshold** | Signal-triggered (momentum + trend confirmation) |
| **Roll/compound trigger** | 12% floating profit → reinvest 80% of position |
| **Max roll tiers** | 4 |
| **Mean reversion** | Disabled (zero) |
| **Stop-loss** | Not explicitly defined in base variant (risk gap) |
| **Take-profit** | Not explicitly defined (trend-riding) |

### Strategy Logic

Pure momentum trend-following. The bot identifies an uptrend, enters with high leverage, and uses **rolling compound reinvestment** — when the position reaches 12% profit, 80% of the profits are reinvested into a larger position, up to 4 tiers. This creates exponential growth during sustained trends without full liquidation risk at each tier (since only profits are rolled, not the entire position).

### When It Works Best

- **Strong directional bull markets** with sustained upward momentum
- **Low volatility regimes** where trends persist without violent pullbacks
- **BTC-dominant rallies** (the 0.85 long bias indicates BTC focus)
- **Post-breakout periods** after consolidation ranges resolve upward

### Key Risk Factors

- **No defined stop-loss** in base variant — vulnerable to sharp reversals
- **Long bias of 0.85** means the bot is essentially blind to bear markets
- **Roll compounding** amplifies losses if the trend reverses mid-compound
- **Extreme leverage (150x)** means even a 0.67% adverse move wipes the margin

### Adaptation Mechanism

The **Newbie Trend Escape v2** variant demonstrates the correct adaptation:
- Add **regime-switch detection** (sensitivity 0.40) — auto-closes positions on trend reversal
- Implement **volatility-adjusted leverage** — reduce leverage when ATR expands beyond threshold
- Add **time-based exit** — force-close after N bars regardless of PnL to prevent round-trip losses
- **Dynamic roll threshold** — increase from 12% to 15-20% in high-volatility regimes to avoid premature compounding

---

## Pattern 2: Doomsday Ultimate — Hyper-Aggressive with Strict Risk Controls

**Representative Bots:** Doomsday Ultimate, Bulldozer, Trend Chaser

### Core Parameters

| Parameter | Value |
|-----------|-------|
| **Leverage** | 150-200x (dynamic range) |
| **Direction bias** | Long 0.85 |
| **Entry** | MA5 × EMA20 crossover, threshold 0.05 |
| **Exit threshold** | 0.12 (signal deactivation) |
| **Stop-loss** | 4× ATR (volatility-adjusted) |
| **Take-profit** | 12:1 risk-reward ratio |
| **Roll/compound** | 80% reinvest at 12% profit, max 4 tiers |
| **Risk per trade** | 90% of available margin |
| **Cut loss** | 50% position reduction at -2%, full flat at -3% |
| **Trailing stop** | Activates at 4% profit, trails at 2.5× ATR |
| **Signal weights** | Trend 50% / Momentum 35% / Volume 10% / Volatility 5% |

### Strategy Logic

This is the **most complete and well-defined strategy** in the dataset. It combines aggressive trend-following with multiple layers of risk management:

1. **Entry:** MA5 crosses EMA20 with a 0.05 signal threshold — confirms short-term momentum alignment
2. **Initial risk:** 4× ATR stop-loss provides volatility-adjusted breathing room
3. **Reward target:** 12:1 RR ratio means for every 1% risked, the target is 12%
4. **Position protection:** At -2% floating loss, cut 50% of position; at -3%, go flat
5. **Profit locking:** Trailing stop activates at 4% profit, trails at 2.5× ATR — locks in gains during pullbacks
6. **Compounding:** Rolling reinvestment only triggers on confirmed 12% profit

### When It Works Best

- **Trending markets** with clear directional bias (MA/EMA crosses are reliable)
- **Moderate volatility** — ATR-based SL/TP needs stable volatility regimes
- **Liquidity-rich sessions** (US/European overlap) — slippage kills tight SL execution
- **BTC and large-cap alts** — technical patterns are more reliable

### Key Risk Factors

- **MA/EMA cross is lagging** — in choppy/ranging markets, generates false signals and whipsaws
- **90% risk per trade** is extremely aggressive — even with SL, gap-downs can breach stops
- **12:1 RR ratio** is ambitious — requires sustained trends; most trends don't deliver 12R
- **Trailing stop at 2.5× ATR** may be too wide for 150x leverage — a normal pullback triggers exit before target

### Adaptation Mechanism

- **Regime detection:** Add ADX filter — only trade MA/EMA crosses when ADX > 25 (trending market). Disable in ranging markets (ADX < 20)
- **Volatility scaling:** Dynamically adjust leverage based on ATR percentile. When ATR is in top 20% of 30-day range, reduce leverage from 200x → 125x
- **Session filtering:** Only activate during high-liquidity hours (08:00-16:00 UTC) to reduce slippage on SL/TP
- **RR ratio calibration:** Track rolling 30-trade average RR achieved. If actual RR < 6:1 over 20 trades, reduce target to 6:1 and increase win-rate focus

---

## Pattern 3: Apocalypse Warrior — Wide-Stop Trend Rider with Trailing Protection

**Representative Bots:** Apocalypse Warrior

### Core Parameters

| Parameter | Value |
|-----------|-------|
| **Leverage** | 150x (fixed) |
| **Direction bias** | Long 0.85 |
| **Stop-loss** | 5× ATR (wide) |
| **Take-profit** | 10:1 risk-reward ratio |
| **Roll/compound** | 100% reinvest at 10% profit, max 5 tiers |
| **Signal weights** | Trend 45% / Momentum 30% (remainder unspecified) |
| **Moving averages** | MA5 / MA20 crossover system |
| **Trailing stop** | Activates at 3% profit, trails at 3× ATR distance |

### Strategy Logic

This pattern uses a **wider stop-loss (5× ATR)** compared to Pattern 2, giving positions more breathing room. The trade-off is a **10:1 RR ratio** (lower than Pattern 2's 12:1) but with a **higher activation threshold for trailing stops (3% profit vs 4%)**. The full 100% reinvestment at each roll tier (vs 80% in other patterns) creates more aggressive compounding but with higher risk.

The key differentiator: **trailing stop activates earlier** (at 3% profit vs 4%), which means profits are protected sooner, but the wider 3× ATR trailing distance means the bot gives back more before exiting.

### When It Works Best

- **High-volatility bull runs** where wide stops are necessary to survive normal pullbacks
- **Early-stage rallies** where trends are explosive but noisy
- **Altcoin seasons** with extreme momentum but frequent 2-3% intraday pullbacks
- **Post-halving bull market phases**

### Key Risk Factors

- **100% reinvestment** (vs 80%) means each compound tier risks all accumulated profits
- **5× ATR stop at 150x leverage** = approximately 3.3% adverse move before liquidation — still tight
- **5 roll tiers** is aggressive — by tier 4-5, the position size is enormous and any reversal is catastrophic
- **3% trailing activation** may trigger too early in strong trends, cutting winners short

### Adaptation Mechanism

- **Dynamic roll percentage:** Reduce reinvestment from 100% → 70% after 2 consecutive losing trades
- **Volatility-tiered trailing stops:** In high ATR regimes, tighten trailing stop to 2× ATR (wide stops become too expensive). In low ATR regimes, widen to 3.5× ATR
- **Profit-tier de-escalation:** After reaching roll tier 3+, reduce leverage from 150x → 100x to protect accumulated profits
- **Trend-strength gating:** Only activate rolling compounds when the parent trend signal is still active (MA5 > MA20). If trend weakens mid-compound, close all tiers

---

## Pattern 4: Regime-Protected Momentum — Adaptive Trend-Following with Auto-Close

**Representative Bots:** Newbie Trend Escape v2, Doomsday Ultimate (regime aspects)

### Core Parameters

| Parameter | Value |
|-----------|-------|
| **Leverage** | 150x (fixed) |
| **Direction bias** | Long 0.85 |
| **Entry** | Momentum + trend signal (0.05 threshold) |
| **Roll/compound** | 80% reinvest at 12% profit, max 4 tiers |
| **Regime detection** | Sensitivity 0.40 — auto-closes on trend reversal |
| **Mean reversion** | Disabled (pure trend) |
| **Additional protection** | Inherited from Doomsday Ultimate: 4× ATR SL, trailing stop |

### Strategy Logic

This pattern represents an **evolution** of the basic trend-following approach by adding a **regime-switch detection layer**. The key innovation is the sensitivity parameter (0.40) — when the market regime shifts (e.g., from bullish to bearish or from trending to ranging), the bot automatically closes all positions regardless of current PnL.

This addresses the fundamental weakness of pure trend-following bots: **they don't know when the trend has ended**. The regime detector acts as a circuit breaker.

### When It Works Best

- **Transition periods** between market regimes (bull → bear, trend → range)
- **Multi-regime environments** where the bot must survive both trending and ranging periods
- **Longer holding periods** where regime changes are more likely to occur mid-trade
- **Any market condition** where pure trend-following would otherwise round-trip profits

### Key Risk Factors

- **Sensitivity 0.40 is a static value** — may be too aggressive (false exits) in noisy markets or too passive (late exits) in fast crashes
- **Regime detection lag** — by the time the regime is confirmed as changed, significant profits may already be lost
- **Whipsaw risk** in oscillating regimes — the bot may enter on regime A→B signal, then exit on B→A, only to re-enter on A→B again
- **Doesn't define its own SL/TP** — relies on inherited parameters from the base trend strategy

### Adaptation Mechanism

- **Dynamic sensitivity:** Adjust sensitivity based on recent regime stability. If regimes have been stable (low churn for 20+ bars), reduce sensitivity to 0.30 (fewer false exits). If regimes are choppy, increase to 0.50 (faster exits)
- **Multi-timeframe regime confirmation:** Require regime change confirmation on both 1H and 4H timeframes before auto-closing, reducing false signals
- **Regime-specific leverage:** In trending regimes, use 150x. In ranging regimes, reduce to 50x or disable entirely
- **Profit preservation mode:** If cumulative PnL is +X% for the session, reduce sensitivity to 0.25 (be more patient with exits to protect profits)

---

## Comparative Summary

| Pattern | Liquidations | Rule Clarity | Risk Management | Real-Capital Viability | Overall Stability |
|---------|:------------:|:------------:|:---------------:|:----------------------:|:-----------------:|
| **1. Doomsday Sprint** (Momentum Rolling) | ✅ 0 | ⚠️ Medium | ⚠️ Partial | ⚠️ Moderate | ★★★☆☆ |
| **2. Doomsday Ultimate** (Strict Risk Control) | ✅ 0 | ✅ High | ✅ Comprehensive | ✅ Best | ★★★★★ |
| **3. Apocalypse Warrior** (Wide-Stop Rider) | ✅ 0 | ✅ High | ✅ Good | ⚠️ Moderate | ★★★★☆ |
| **4. Regime-Protected Momentum** (Adaptive) | ✅ 0 | ✅ High | ✅ Good | ✅ Good | ★★★★☆ |

---

## Key Findings

### What Makes a Strategy "Stable" in This Dataset

1. **Zero liquidations across all bots** is notable — but this is simulated PnL. In real markets, 150x leverage with 90% risk per trade would liquidate frequently. The zero liquidation count likely reflects idealized execution.

2. **The most stable pattern is Pattern 2 (Doomsday Ultimate)** because it is the only one with a complete risk management stack: defined entry, SL, TP, trailing stop, position reduction rules, AND rolling compounds. Every other pattern is missing at least one of these elements.

3. **Rolling compound reinvestment** (80% at 12% profit, max 4 tiers) is the most reproducible element across patterns. It's a sound approach because it only risks profits, not principal.

4. **Regime detection** (Pattern 4) is the critical missing piece in most bots. The fact that only one bot implements it suggests this is the highest-value improvement for making these strategies production-ready.

### Critical Gaps for Real-Capital Deployment

| Gap | Impact | Fix |
|-----|--------|-----|
| No short/bear strategies | All bots are long-biased (0.85) — useless in bear markets | Add short-bias variants with mirrored parameters |
| No slippage modeling | 150x leverage + tight SLs + real orderbooks = guaranteed slippage | Reduce leverage to 25-50x, widen SL to 8-10× ATR |
| No position sizing across portfolio | 90% risk per trade is portfolio suicide | Kelly criterion or fixed fractional (1-2% risk per trade) |
| No correlation management | All bots trade similar signals — concentrated risk | Add correlation filters, diversify across uncorrelated signals |
| Simulated PnL inflates confidence | Real capital would see 50-90% lower returns | Stress-test with 2022 bear market data |

### Recommendation for Production

The **Doomsday Ultimate** pattern (Pattern 2) is the strongest foundation. To make it production-ready:

1. **Reduce leverage from 150x → 25-50x** (survivable with real capital)
2. **Reduce risk per trade from 90% → 5-10%** (Kelly-adjusted position sizing)
3. **Add regime detection** from Pattern 4 (circuit breaker for trend reversals)
4. **Add short-bias variant** (mirror all parameters for bear markets)
5. **Backtest on 2022 bear market data** to validate SL/TP behavior in sustained downtrends

---

*Analysis generated: 2026-04-13*
*Dataset: 15 bots from Moss.ai platform (of 30 total referenced)*
*Next step: Round 2 analysis after feedback on these patterns*
