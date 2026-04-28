import json
import subprocess


def test_cli_demo_json_output():
    p = subprocess.run(["python", "-m", "trade_core.cli", "demo", "--sample", "examples/full_case.json"], capture_output=True, text=True, check=True)
    data = json.loads(p.stdout)
    assert "decision" in data
    assert "order_intent" in data
