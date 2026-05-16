"""Pytest configuration for unit tests.

Adds the unit-tests directory to ``sys.path`` so reusable test helpers under
``tests/unit/helpers/`` can be imported as ``helpers.<module>`` from any unit
test without making ``tests`` itself a Python package.
"""

from __future__ import annotations

import sys
from pathlib import Path

_UNIT_DIR = Path(__file__).resolve().parent
if str(_UNIT_DIR) not in sys.path:
    sys.path.insert(0, str(_UNIT_DIR))
