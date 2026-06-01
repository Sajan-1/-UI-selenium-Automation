import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "testes.py"

def test_classlens_run_all():
    assert RUNNER.exists(), f"Runner not found: {RUNNER}"

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["RICH_FORCE_TERMINAL"] = "1"
    env["TERM"] = "xterm-256color"

    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(RUNNER), "--run-all"],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=7200,
        env=env
    )

    assert result.returncode == 0, (
        "ClassLens run failed\n\nSTDOUT:\n"
        + result.stdout[-10000:]
        + "\n\nSTDERR:\n"
        + result.stderr[-10000:]
    )
