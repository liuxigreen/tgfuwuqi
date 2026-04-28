from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config, validate_config
from .daily_limits import limits_reset, limits_status
from .fast_path import run_fast_signal_pipeline
from .journal import review_journal
from .lifecycle import run_demo_execution_pipeline, run_position_management, run_pretrade_pipeline
from .models import model_to_dict
from .okx_gateway import OkxGateway
from .reporting import build_daily_report
from .replay import replay_case, replay_journal
from .scout import run_scout
from .self_evolution import build_proposal, daily_review, save_proposal, validate_proposal
from .signal_bus import parse_case_payload


def _read_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _build_gateway(cfg: dict) -> OkxGateway:
    return OkxGateway(backend=cfg.get("backend", "mock"), profile=cfg.get("profile", "demo"), dry_run=True, allow_live=cfg.get("allow_live", False), allow_trade_execution=cfg.get("allow_trade_execution", False), command_timeout_seconds=int(cfg.get("command_timeout_seconds", 20)))


def main() -> None:
    parser = argparse.ArgumentParser(prog="trade_core.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate-config")
    for cmd in ["demo", "propose"]:
        p = sub.add_parser(cmd); p.add_argument("--sample", required=True)

    fs = sub.add_parser("fast-signal"); fs.add_argument("--sample", required=True); fs.add_argument("--mode", default="propose"); fs.add_argument("--demo-execute", action="store_true")
    sub.add_parser("limits-status")
    lr = sub.add_parser("limits-reset"); lr.add_argument("--date", required=True)

    rep = sub.add_parser("replay"); rep.add_argument("--journal", required=False); rep.add_argument("--events", required=False)
    c = sub.add_parser("okx-check"); c.add_argument("--backend", default=None); c.add_argument("--profile", default=None)
    m = sub.add_parser("okx-market"); m.add_argument("--symbol", required=True)
    sub.add_parser("okx-account")
    s = sub.add_parser("scout"); s.add_argument("--symbols", required=True); s.add_argument("--mode", default="propose")
    p = sub.add_parser("pipeline"); p.add_argument("--sample", required=True); p.add_argument("--mode", default="propose")
    e = sub.add_parser("execute"); e.add_argument("--sample", required=True); e.add_argument("--backend", default="cli"); e.add_argument("--profile", default="demo"); e.add_argument("--demo-execute", action="store_true")
    mg = sub.add_parser("manage-position"); mg.add_argument("--sample", required=True)
    rv = sub.add_parser("review"); rv.add_argument("--journal", required=True)
    rp = sub.add_parser("report"); rp.add_argument("--journal", required=True)
    dr = sub.add_parser("daily-review"); dr.add_argument("--date", required=True)
    se = sub.add_parser("self-evolve"); se.add_argument("--date", required=True)

    args = parser.parse_args(); config = load_config()

    if args.cmd == "validate-config": print(json.dumps(validate_config(config), ensure_ascii=False)); return
    if args.cmd == "limits-status": print(json.dumps(limits_status(), ensure_ascii=False)); return
    if args.cmd == "limits-reset": print(json.dumps(limits_reset(args.date), ensure_ascii=False)); return

    if args.cmd in {"demo", "propose"}:
        payload = parse_case_payload(_read_json(args.sample)); mode = "demo_auto" if args.cmd == "demo" else "propose"
        from .decision import build_trade_decision
        from .order_intent import build_order_intent
        decision = build_trade_decision(radar_signal=payload["radar_signal"], nuwa_eval=payload["nuwa_eval"], market_snapshot=payload.get("market_snapshot"), sentiment_snapshot=payload.get("sentiment_snapshot"), smartmoney_snapshot=payload.get("smartmoney_snapshot"), account_snapshot=payload.get("account_snapshot"), mode=mode, config=config)
        intent = build_order_intent(decision, config=config)
        print(json.dumps({"decision": model_to_dict(decision), "order_intent": model_to_dict(intent)}, ensure_ascii=False)); return

    if args.cmd == 'fast-signal':
        print(json.dumps(run_fast_signal_pipeline(_read_json(args.sample), mode=args.mode, demo_execute=args.demo_execute), ensure_ascii=False)); return

    if args.cmd == "replay":
        if args.journal: print(json.dumps(replay_journal(args.journal), ensure_ascii=False)); return
        print(json.dumps(replay_case(_read_json(args.events), config), ensure_ascii=False)); return

    gw_cfg = dict(config["okx_gateway"])
    if args.cmd == "okx-check":
        if args.backend: gw_cfg["backend"] = args.backend
        if args.profile: gw_cfg["profile"] = args.profile
        gw = _build_gateway(gw_cfg)
        print(json.dumps({"okx_check": gw.okx_check(), "gateway_config": gw_cfg}, ensure_ascii=False)); return
    if args.cmd == "okx-market":
        gw = _build_gateway(gw_cfg)
        print(json.dumps({"ticker": gw.get_ticker(args.symbol), "candles": gw.get_candles(args.symbol), "funding": gw.get_funding_rate(args.symbol), "open_interest": gw.get_open_interest(args.symbol)}, ensure_ascii=False)); return
    if args.cmd == "okx-account":
        gw = _build_gateway(gw_cfg)
        print(json.dumps({"profile": gw.profile, "warning": "non_demo_profile" if gw.profile != "demo" else None, "balance": gw.get_balance(), "positions": gw.get_positions(), "account_snapshot": gw.get_account_snapshot()}, ensure_ascii=False)); return
    if args.cmd == "scout":
        gw = _build_gateway(gw_cfg)
        print(json.dumps(run_scout([x.strip() for x in args.symbols.split(",") if x.strip()], args.mode, gw), ensure_ascii=False)); return
    if args.cmd == "pipeline": print(json.dumps(run_pretrade_pipeline(_read_json(args.sample), mode=args.mode), ensure_ascii=False)); return
    if args.cmd == "execute": print(json.dumps(run_demo_execution_pipeline(_read_json(args.sample), demo_execute=args.demo_execute, backend=args.backend, profile=args.profile), ensure_ascii=False)); return
    if args.cmd == "manage-position": print(json.dumps(run_position_management(_read_json(args.sample)), ensure_ascii=False)); return
    if args.cmd == "review": print(json.dumps(review_journal(args.journal), ensure_ascii=False)); return
    if args.cmd == "report": print(json.dumps(model_to_dict(build_daily_report(args.journal)), ensure_ascii=False)); return
    if args.cmd == 'daily-review': print(json.dumps(daily_review(args.date), ensure_ascii=False)); return
    if args.cmd == 'self-evolve':
        rev = daily_review(args.date)
        if not rev.get('ok'):
            print(json.dumps(rev, ensure_ascii=False)); return
        prop = build_proposal(args.date, rev)
        guard = validate_proposal(prop)
        path = save_proposal(args.date, prop)
        print(json.dumps({**prop, "guardrails": guard, "proposal_path": path}, ensure_ascii=False)); return


if __name__ == "__main__":
    main()
