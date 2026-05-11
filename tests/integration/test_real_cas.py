"""Integration tests that run against a real CAS PDF fixture.

Skipped automatically in CI (no fixture file). Run locally after placing
a sanitised PDF in tests/integration/fixtures/ — see README.md there.
"""

import os
from pathlib import Path

import pytest
from starlette.testclient import TestClient

FIXTURE_DIR = Path(__file__).parent / "fixtures"
CAMS_PDF = FIXTURE_DIR / "cams_sample.pdf"
CAMS_PASSWORD = os.getenv("CAS_FIXTURE_PASSWORD", "")


@pytest.mark.integration
@pytest.mark.skipif(not CAMS_PDF.exists(), reason="no fixture PDF")
def test_real_cams_import(client: TestClient) -> None:
    client.post(
        "/api/setup",
        json={"individual_name": "Test User", "household_name": "Test Family"},
    )
    with CAMS_PDF.open("rb") as f:
        resp = client.post(
            "/api/import/cas",
            files={"file": ("cams_sample.pdf", f, "application/pdf")},
            data={"password": CAMS_PASSWORD},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["imported"] > 0
    assert body["as_of"] is not None
    assert float(body["total"]) > 0
