"""Shared pytest configuration."""

import os
import sys
from pathlib import Path

# Headless matplotlib for CI and local test runs
os.environ.setdefault("MPLBACKEND", "Agg")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
