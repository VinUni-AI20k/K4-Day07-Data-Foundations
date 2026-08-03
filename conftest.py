"""Load pytest configuration before the solution package is imported.

An explicit shell variable wins over `.env`; `.env` wins over the personal
package default below.  This keeps the shared test suite usable for every
member while making `dev/chien` test Dao Minh Chien's package by default.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).parent / ".env", override=False)
os.environ.setdefault(
    "LAB_SOLUTION_PACKAGE",
    "src.K4_2A202601184_DaoMinhChien",
)
