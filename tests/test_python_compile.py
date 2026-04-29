import subprocess


def test_trade_core_python_compile():
    cmd = "python -m py_compile $(find trade_core -name '*.py')"
    res = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
