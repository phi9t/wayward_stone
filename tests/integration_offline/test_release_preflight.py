from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration_offline
def test_release_preflight_no_docker(repo_root: Path) -> None:
    proc = subprocess.run(
        ["./scripts/release_preflight.sh", "--no-docker"],
        cwd=repo_root,
        env={**os.environ, "AUDIOBOOK_SKIP_BUILD": "1", "AUDIOBOOK_USE_GPU": "1"},
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Release preflight complete" in proc.stdout
