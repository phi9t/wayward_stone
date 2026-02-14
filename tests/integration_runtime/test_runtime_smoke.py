from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.runtime


def runtime_enabled() -> bool:
    return os.environ.get("RUN_RUNTIME_INTEGRATION") == "1"


@pytest.mark.skipif(not runtime_enabled(), reason="Set RUN_RUNTIME_INTEGRATION=1 to run runtime integration tests")
def test_verify_spack_provenance_runtime(repo_root: Path) -> None:
    proc = subprocess.run(
        ["./audiobook/verify_zephyr_spack_provenance.sh"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK: torch and jax are from Spack" in proc.stdout


@pytest.mark.skipif(not runtime_enabled(), reason="Set RUN_RUNTIME_INTEGRATION=1 to run runtime integration tests")
def test_run_book_batch_wrapper_runtime_smoke(repo_root: Path) -> None:
    env = {
        **os.environ,
        "AUDIOBOOK_USE_GPU": "1",
        "AUDIOBOOK_SKIP_BUILD": "1",
    }
    proc = subprocess.run(
        ["./audiobook/run_book_batch_zephyr.sh", "--", "--help"],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Batch render chapters with Qwen3-TTS" in proc.stdout
