from __future__ import annotations

import os
import subprocess

import pytest

pytestmark = pytest.mark.runtime


def runtime_enabled() -> bool:
    return os.environ.get("RUN_RUNTIME_INTEGRATION") == "1"


@pytest.mark.skipif(not runtime_enabled(), reason="Set RUN_RUNTIME_INTEGRATION=1 to run runtime integration tests")
def test_agent_clis_available() -> None:
    for cmd in (["codex", "exec", "--help"], ["opencode", "run", "--help"], ["claude", "--help"]):
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
        assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.skipif(not runtime_enabled(), reason="Set RUN_RUNTIME_INTEGRATION=1 to run runtime integration tests")
def test_inkforge_script_help() -> None:
    proc = subprocess.run(["python", "scripts/inkforge_loop.py", "run", "--help"], text=True, capture_output=True, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "--target-chapter" in proc.stdout
