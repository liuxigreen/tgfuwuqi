from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config, validate_config
from .decision import build_trade_decision
from .models import model_to_dict
from .order_intent import build_order_intent
from .replay import replay_case
from .signal_bus import parse_case_payload


def _read_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(prog="trade_core.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate-config")

    demo = sub.add_parser("demo")
    demo.add_argument("--sample", required=True)

    propose = sub.add_parser("propose")
    propose.add_argument("--sample", required=True)

    replay_cmd = sub.add_parser("replay")
    replay_cmd.add_argument("--events", required=True)

    args = parser.parse_args()
    config = load_config()

    if args.cmd == "validate-config":
        print(json.dumps(validate_config(config), ensure_ascii=False))
        return

    if args.cmd in {"demo", "propose"}:
        payload = parse_case_payload(_read_json(args.sample))
        mode = "demo_auto" if args.cmd == "demo" else "propose"
        decision = build_trade_decision(
            radar_signal=payload["radar_signal"],
            nuwa_eval=payload["nuwa_eval"],
            market_snapshot=payload.get("market_snapshot"),
            sentiment_snapshot=payload.get("sentiment_snapshot"),
            smartmoney_snapshot=payload.get("smartmoney_snapshot"),
            account_snapshot=payload.get("account_snapshot"),
            mode=mode,
            config=config,
        )
        intent = build_order_intent(decision, config=config)
        print(json.dumps({"decision": model_to_dict(decision), "order_intent": model_to_dict(intent)}, ensure_ascii=False))
        return

    if args.cmd == "replay":
        data = _read_json(args.events)
        print(json.dumps(replay_case(data, config), ensure_ascii=False))
        return


if __name__ == "__main__":
    main()
