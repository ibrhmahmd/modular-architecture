"""OpenAPI snapshot: any change to the API's shape fails this test.

Regenerate only in a ticket that names an API change:
    UPDATE_OPENAPI_SNAPSHOT=1 pytest tests/architecture/test_openapi_snapshot.py
Edit the import below to point at the app factory.
"""

import difflib
import json
import os
from pathlib import Path

import pytest

from app.main import create_app  # EDIT: the project's app factory

SNAPSHOT_PATH = Path(__file__).resolve().parents[1] / "snapshots" / "openapi.json"
_PREVIEW_LINES = 80


def current_spec() -> str:
    return json.dumps(create_app().openapi(), indent=2, sort_keys=True) + "\n"


def test_openapi_snapshot():
    if os.environ.get("UPDATE_OPENAPI_SNAPSHOT") == "1":
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(current_spec(), encoding="utf-8")
        return
    if not SNAPSHOT_PATH.exists():
        pytest.fail(f"{SNAPSHOT_PATH} is missing; create it with UPDATE_OPENAPI_SNAPSHOT=1")

    expected = SNAPSHOT_PATH.read_text(encoding="utf-8")
    actual = current_spec()
    if actual == expected:
        return
    diff = list(difflib.unified_diff(expected.splitlines(), actual.splitlines(), "snapshot", "generated", lineterm=""))
    more = len(diff) - _PREVIEW_LINES
    message = "\n".join(diff[:_PREVIEW_LINES]) + (f"\n... and {more} more lines" if more > 0 else "")
    pytest.fail(f"OpenAPI spec changed. If a ticket names this change, regenerate with UPDATE_OPENAPI_SNAPSHOT=1.\n\n{message}")
