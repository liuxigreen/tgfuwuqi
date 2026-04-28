import subprocess


CMDS = [
    "python -m trade_core.cli validate-config",
    "python -m trade_core.cli fast-signal --sample examples/fast_signal_long_case.json --mode propose",
    "python -m trade_core.cli fast-signal --sample examples/fast_signal_long_case.json --mode demo_auto",
    "python -m trade_core.cli limits-status",
    "python -m trade_core.cli daily-review --date 2026-04-28",
    "python -m trade_core.cli self-evolve --date 2026-04-28",
    "python -m trade_core.cli okx-check",
]


def test_cli_commands_stable():
    for cmd in CMDS:
        res = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True)
        assert res.returncode == 0, f"{cmd}\n{res.stderr}\n{res.stdout}"
