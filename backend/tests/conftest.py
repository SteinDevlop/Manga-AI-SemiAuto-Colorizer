"""Pytest configuration for Manga Colorizer backend tests.

Adds ``backend/`` to ``sys.path`` so ``app.*`` imports resolve from the
repository root.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
