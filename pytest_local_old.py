# Auto-generated add-only pytest wrapper for ClassLens master runner.
import os
import sys
import subprocess
from pathlib import Path

def test_classlens_master_runner_all_tabs_headless_nonstop():
    root = Path(__file__).resolve().parent
    script = root / 'classlens_combined_NONSTOP_pytest_headless_TIMED_V4.py'
    env = os.environ.copy()
    env['CLASSLENS_HEADLESS'] = '1'
    env['CLASSLENS_FAST_MODE'] = '1'
    env['CLASSLENS_FAST_MAX_SLEEP'] = '0.15'
    env.setdefault('CLASSLENS_MODULE_TIMEOUT', '360')
    args = [sys.executable, str(script), '--all', '--headless', '--module-timeout', env['CLASSLENS_MODULE_TIMEOUT']]
    proc = subprocess.run(args, cwd=str(root), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=int(env['CLASSLENS_MODULE_TIMEOUT']) * 5 + 180)
    assert proc.returncode == 0, proc.stdout[-16000:]
