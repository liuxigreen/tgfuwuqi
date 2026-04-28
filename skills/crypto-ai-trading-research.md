---
name: crypto-ai-trading-research
description: AI-driven crypto futures trading system research — analyzing winning strategies from Moss.site, building adaptive trading bots with Qwen analysis pipeline.
tags: [devops, crypto, trading, ai, qwen]
related_skills: [agenthansa-automation]
---

# Crypto AI Trading Research

Automated research pipeline for building adaptive crypto futures trading bots. Uses Qwen Code CLI for iterative strategy analysis.

## Data Sources

### Moss.site AI Trading Arena
- **API Base**: `https://ai.moss.site/api/v1/`
- **Backtest leaderboard**: `GET /moss/agent/trader/discover/leaderboard?mode=hell`
- **Live bots**: `GET /moss/agent/trader/bots?language=en&mode=realtime&page=1&page_size=50&sort_by=pnl&sort_order=desc`
- **Public stats**: `GET /trade/trader-stats/public?limit=20&offset=0&order_field=total_pnl&order_order=desc`
- Discovery: API endpoints found via `performance.getEntriesByType('resource')` in browser console
- ⚠️ PnL numbers are simulated (trillions of dollars) — focus on STRATEGY PATTERNS not absolute returns

### DegenClaw (Virtuals Protocol)
- `https://degen.virtuals.io/agents/580` — "Fat Tiger" agent
- Subscription: 10 USDC/mo to see trading data
- Not yet started trading (Season 3 ended)

## Qwen Code CLI

**Location**: `/usr/local/bin/qwen` (standalone binary, NOT npx)

```bash
# Basic usage
qwen "your prompt" -o json --approval-mode yolo

# Parse output
echo '...' | python3 -c "
import sys, json
data = json.loads(sys.stdin.read())
for e in data:
    if e.get('type') == 'result':
        print(e.get('result', ''))
        break
"
```

- Output: JSON array of events, extract `type=="result"`
- Timeout: ~180s
- Save large context to file first, then tell Qwen to read it — don't inline huge data in prompt

## Iterative Research Pipeline (10 rounds)

1. Save data to `/root/.hermes/agenthansa/memory/qwen-research/`
2. Prepare focused input file with context + specific task
3. Run Qwen: `qwen "Read file X, follow instructions, save to Y" -o json --approval-mode yolo`
4. Review output, feed back into next iteration
5. Each round refines: patterns → parameters → adaptation mechanisms → implementation plan

## Key Findings (Round 1 — 2026-04-13)

### Top 4 Stable Strategy Patterns from Moss

**1. Doomsday Ultimate — Strict Risk Control (★★★★★)**
- Leverage: 150-200x (for simulation; real capital: 25-50x)
- Direction: Long bias 0.85
- Entry: MA5 × EMA20 crossover, threshold 0.05
- Exit: signal deactivation at 0.12
- SL: 4× ATR (volatility-adjusted)
- TP: 12:1 risk-reward ratio
- Rolling: 12% profit → 80% reinvest, max 4 tiers
- Signal weights: Trend 50 / Momentum 35 / Volume 10 / Volatility 5
- Risk: Cut 50% at -2%, flat at -3%
- Trail SL: Activate at 4% profit, 2.5 ATR trailing

**2. Regime-Protected Momentum (★★★★)**
- Same as #1 + regime-switch detection (sensitivity 0.40)
- Auto-closes positions on trend reversal
- Best adaptation mechanism found

**3. Apocalypse Warrior — Wide-Stop Rider (★★★★)**
- Wider stops (5× ATR), earlier trailing (3% activation)
- Better in noisy bull markets
- 100% reinvestment is aggressive

**4. Doomsday Sprint — Rolling Momentum (★★★)**
- Pure trend-following, no defined SL/TP
- Clean logic but vulnerable to reversals

### Critical Real-Capital Adjustments
- **Leverage**: Must drop to 25-50x (from 150x simulated)
- **Risk per trade**: 5-10% (from 50-90% simulated)
- **Direction bias**: Consider 0.5-0.6 instead of 0.85 (need short capability)
- **Rolling**: Reduce to 50% reinvest max (from 80-100%)

## DegenClaw / Virtuals Protocol
- Agent #580 "Fat Tiger": Season 3 ended, hasn't started trading
- 10 USDC/mo subscription to see data
- Token burnt: 10,038,452.55 (1.004% of supply)
- Not useful for strategy analysis yet

## Twitter Reference (user provided)
- https://x.com/zeroxmin/status/2038600565895340447 — couldn't access (login wall)
- Use nitter instances or browser to extract if needed

## Pending Questions for User
1. Which exchange? (Binance/OKX/Bybit)
2. Starting capital amount
3. Max acceptable daily loss
4. Paper trade first or live immediately

## File Layout
```
/root/.hermes/agenthansa/memory/qwen-research/
├── crypto-context.md          # Research context + data summary
├── crypto-round1.md           # Qwen Round 1 analysis
├── moss-data.json             # Raw API data (50 live bots)
├── moss-compact.json          # Simplified bot summaries
├── qwen-input-1.txt           # Round 1 prompt for Qwen
└── crypto-round[2-10].md      # Future iterations
```

## Pitfalls
- Moss "live" PnL is simulated (trillions) — don't trust absolute numbers
- All bots are long-biased 0.85 with zero liquidations — clearly not real trading
- Qwen timeout: 180s max, keep prompts focused
- Save data to file before running Qwen — don't inline in prompt
