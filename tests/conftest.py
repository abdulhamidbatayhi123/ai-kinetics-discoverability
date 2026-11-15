"""Shared set-up: every test runs from the repository root, whatever directory pytest was started in.

The modules under test open their inputs by paths relative to the repository root (for example
p2_observe.DATA = "data/p2"), as they do when run from the command line.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _run_from_repository_root(monkeypatch):
    monkeypatch.chdir(ROOT)
