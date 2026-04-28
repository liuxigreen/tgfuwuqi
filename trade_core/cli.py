from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config, validate_config
from .journal import review_journal
from .lifecycle import run_demo_execution_pipeline, run_position_management, run_pretrade_pipeline
from .models import model_to_dict
from .okx_gateway import OkxGateway
from .replay import replay_case
from .scout import run_scout
from .signal_bus import parse_case_payload


def _read_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _build_gateway(cfg: dict) -> OkxGateway:
    return OkxGateway(
        backend=cfg.get("backend", "mock"),
        profile=cfg.get("profile", "demo"),
        dry_run=True,
        allow_live=cfg.get("allow_live", False),
        allow_trade_execution=cfg.get("allow_trade_execution", False),
        command_timeout_seconds=int(cfg.get("command_timeout_seconds", 20)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="trade_core.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate-config")

    for cmd in ["demo", "propose"]:
        p = sub.add_parser(cmd)
        p.add_argument("--sample", required=True)

    replay_cmd = sub.add_parser("replay")
    replay_cmd.add_argument("--events", required=True)

    okx_check = sub.add_parser("okx-check")
    okx_check.add_argument("--backend", default=None)
    okx_check.add_argument("--profile", default=None)

    okx_market = sub.add_parser("okx-market")
    okx_market.add_argument("--symbol", required=True)

    sub.add_parser("okx-account")

    scout_cmd = sub.add_parser("scout")
    scout_cmd.add_argument("--symbols", required=True)
    scout_cmd.add_argument("--mode", default="propose")

    pipe_cmd = sub.add_parser("pipeline")
    pipe_cmd.add_argument("--sample", required=True)
    pipe_cmd.add_argument("--mode", default="propose")

    exec_cmd = sub.add_parser("execute")
    exec_cmd.add_argument("--sample", required=True)
    exec_cmd.add_argument("--backend", default="cli")
    exec_cmd.add_argument("--profile", default="demo")
    exec_cmd.add_argument("--demo-execute", action="store_true")

    manage_cmd = sub.add_parser("manage-position")
    manage_cmd.add_argument("--sample", required=True)

    review_cmd = sub.add_parser("review")
    review_cmd.add_argument("--journal", required=True)

    args = parser.parse_args()
    config = load_config()

    if args.cmd == "validate-config":
        print(json.dumps(validate_config(config), ensure_ascii=False))
        return

    if args.cmd in {"demo", "propose"}:
        payload = parse_case_payload(_read_json(args.sample))
        mode = "demo_auto" if args.cmd == "demo" else "propose"
        from .decision import build_trade_decision
        from .order_intent import build_order_intent

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
        print(json.dumps(replay_case(_read_json(args.events), config), ensure_ascii=False))
        return

    gw_cfg = dict(config["okx_gateway"])
    if args.cmd == "okx-check":
        if args.backend:
            gw_cfg["backend"] = args.backend
        if args.profile:
            gw_cfg["profile"] = args.profile
        gw = _build_gateway(gw_cfg)
        print(json.dumps({"okx_check": gw.okx_check(), "gateway_config": gw_cfg}, ensure_ascii=False))
        return

    if args.cmd == "okx-market":
        gw = _build_gateway(gw_cfg)
        out = {
            "ticker": gw.get_ticker(args.symbol),
            "candles": gw.get_candles(args.symbol),
            "funding": gw.get_funding_rate(args.symbol),
            "open_interest": gw.get_open_interest(args.symbol),
        }
        print(json.dumps(out, ensure_ascii=False))
        return

    if args.cmd == "okx-account":
        gw = _build_gateway(gw_cfg)
        out = {"profile": gw.profile, "warning": "non_demo_profile" if gw.profile != "demo" else None, "balance": gw.get_balance(), "positions": gw.get_positions(), "account_snapshot": gw.get_account_snapshot()}
        print(json.dumps(out, ensure_ascii=False))
        return

    if args.cmd == "scout":
        gw = _build_gateway(gw_cfg)
        print(json.dumps(run_scout([s.strip() for s in args.symbols.split(",") if s.strip()], args.mode, gw), ensure_ascii=False))
        return

    if args.cmd == "pipeline":
        print(json.dumps(run_pretrade_pipeline(_read_json(args.sample), mode=args.mode), ensure_ascii=False))
        return

    if args.cmd == "execute":
        sample = _read_json(args.sample)
        result = run_demo_execution_pipeline(sample, demo_execute=args.demo_execute)
        print(json.dumps({"backend": args.backend, "profile": args.profile, "demo_execute": args.demo_execute, "result": result}, ensure_ascii=False))
        return

    if args.cmd == "manage-position":
        print(json.dumps(run_position_management(_read_json(args.sample)), ensure_ascii=False))
        return

    if args.cmd == "review":
        print(json.dumps(review_journal(args.journal), ensure_ascii=False))
        return


if __name__ == "__main__":
    main()
