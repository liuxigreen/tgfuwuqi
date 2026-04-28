# Scheduler Ready Commands

未来可由 cron/systemd/Hermes/OpenClaw 调度：

- `python -m trade_core.cli scout --symbols BTC-USDT-SWAP,ETH-USDT-SWAP --mode propose`
- `python -m trade_core.cli pipeline --sample examples/full_case.json --mode propose`
- `python -m trade_core.cli manage-position --sample examples/position_case.json`
- `python -m trade_core.cli review --journal data/trade_core_journal/YYYY-MM-DD.trade_core.jsonl`
- `python -m trade_core.cli report --journal data/trade_core_journal/YYYY-MM-DD.trade_core.jsonl`

当前不创建真实 cron/systemd 任务。
