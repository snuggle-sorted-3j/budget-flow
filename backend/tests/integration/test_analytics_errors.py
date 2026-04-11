"""
Integration tests for analytics endpoint error paths and uncovered happy paths.
Covers: category-trends 404, compare-periods 404, recurring-patterns 200, anomalies 200.
"""
import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient


class TestAnalyticsErrors:

    def test_category_trends_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """GET category-trends with non-existent category_id returns 404."""
        resp = client.get(
            f"/api/v1/analytics/category-trends/{uuid.uuid4()}",
            headers=auth_headers
        )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_compare_periods_not_found_returns_404(
        self, client: TestClient, auth_headers: Dict
    ):
        """GET compare-periods with non-existent period IDs returns 404."""
        resp = client.get(
            f"/api/v1/analytics/compare-periods",
            params={
                "period_id_1": str(uuid.uuid4()),
                "period_id_2": str(uuid.uuid4())
            },
            headers=auth_headers
        )
        assert resp.status_code == 404

    def test_recurring_patterns_returns_200(
        self, client: TestClient, auth_headers: Dict
    ):
        """GET recurring-patterns returns 200 with list."""
        resp = client.get("/api/v1/analytics/recurring-patterns", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_anomalies_returns_200(
        self, client: TestClient, auth_headers: Dict, test_currency, test_category
    ):
        """GET anomalies with valid period_id returns 200."""
        period_resp = client.post("/api/v1/periods/", json={
            "period_name": f"AnomalyPeriod-{uuid.uuid4().hex[:6]}",
            "start_date": "2026-05-01",
            "end_date": "2026-05-31",
            "snapshot_date": "2026-05-31"
        }, headers=auth_headers)
        assert period_resp.status_code == 201
        period_id = period_resp.json()["id"]

        resp = client.get(
            "/api/v1/analytics/anomalies",
            params={"period_id": period_id},
            headers=auth_headers
        )
        assert resp.status_code == 200
