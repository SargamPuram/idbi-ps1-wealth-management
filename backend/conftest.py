"""
Makes the backend package tree (`advisory`, `app`) importable during pytest
runs regardless of the working directory the suite is invoked from (repo
root vs. backend/). pytest auto-discovers conftest.py files by walking up
from each test file's directory, so this is picked up for anything under
backend/tests/ without any extra config.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
