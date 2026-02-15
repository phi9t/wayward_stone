#!/usr/bin/env python3
import sys
from pathlib import Path

# Ensure repo root is on sys.path so the inkforge_loop package is importable
# when this script is invoked directly (e.g. python scripts/inkforge_loop.py).
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from inkforge_loop.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
