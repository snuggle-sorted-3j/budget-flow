"""
Integration tests for /api/v1/periods endpoints.

Covers:
- POST /periods          — create period (201), validation errors (422)
- GET /periods           — list periods for current user
- GET /periods/{id}      — get specific period (200 and 404)
- PATCH /periods/{id}/status — update period status (200 and 404)
- DELETE /periods/{id}   — delete period (200 and 404)
- Auth checks            — 401 without token on every route
"""

import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient

from app.models.user import User

BASE_URL = "/api/v1/periods"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_PERIOD_PAYLOAD = {
    "period_name": "Test Period Jan 2026",
    "start_date": "2026-01-01",
    "end_date": "2026-01-31",
    "snapshot_date": "2026-01-31",
}


def create_period(client: TestClient, auth_headers: Dict, payload: dict = None) -> dict:
    """Helper: POST a period and return its JSON."""
    payload = payload or VALID_PERIOD_PAYLOAD
    resp = client.post(f"{BASE_URL}/", json=payload, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ===========================================================================
# POST /periods/
# ===========================================================================


def test_create_period_success(client: TestClient, auth_headers: Dict):
    """Creating a valid period returns 201 with correct fields."""
    resp = client.post(f"{BASE_URL}/", json=VALID_PERIOD_PAYLOAD, headers=auth_headers)

    assert resp.status_code == 201
    data = resp.json()
    assert data["period_name"] == VALID_PERIOD_PAYLOAD["period_name"]
    assert data["start_date"] == VALID_PERIOD_PAYLOAD["start_date"]
    assert data["end_date"] == VALID_PERIOD_PAYLOAD["end_date"]
    assert data["snapshot_date"] == VALID_PERIOD_PAYLOAD["snapshot_date"]
    assert data["status"] == "DRAFT"
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_period_returns_201_status_code(client: TestClient, auth_headers: Dict):
    """Explicit check that 201 Created is returned (not 200)."""
    resp = client.post(f"{BASE_URL}/", json=VALID_PERIOD_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 201


def test_create_period_missing_required_fields(client: TestClient, auth_headers: Dict):
    """Missing required fields returns 422 Unprocessable Entity."""
    resp = client.post(f"{BASE_URL}/", json={}, headers=auth_headers)
    assert resp.status_code == 422


def test_create_period_missing_period_name(client: TestClient, auth_headers: Dict):
    """Missing period_name returns 422."""
    payload = {
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "snapshot_date": "2026-01-31",
    }
    resp = client.post(f"{BASE_URL}/", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_create_period_snapshot_date_must_equal_end_date(client: TestClient, auth_headers: Dict):
    """snapshot_date must equal end_date; otherwise 422."""
    payload = {
        "period_name": "Bad Snapshot",
        "start_date": "2026-01-01",
        "end_date": "2026-01-31",
        "snapshot_date": "2026-01-15",  # <-- mismatch
    }
    resp = client.post(f"{BASE_URL}/", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_create_period_end_date_before_start_date(client: TestClient, auth_headers: Dict):
    """end_date before start_date returns 422."""
    payload = {
        "period_name": "Bad Dates",
        "start_date": "2026-02-01",
        "end_date": "2026-01-01",  # <-- before start
        "snapshot_date": "2026-01-01",
    }
    resp = client.post(f"{BASE_URL}/", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_create_period_no_auth(client: TestClient):
    """Creating a period without a token returns 401."""
    resp = client.post(f"{BASE_URL}/", json=VALID_PERIOD_PAYLOAD)
    assert resp.status_code == 401


def test_create_period_invalid_token(client: TestClient):
    """Creating a period with a bad token returns 401."""
    resp = client.post(
        f"{BASE_URL}/",
        json=VALID_PERIOD_PAYLOAD,
        headers={"Authorization": "Bearer this.is.not.valid"},
    )
    assert resp.status_code == 401


# ===========================================================================
# GET /periods/
# ===========================================================================


def test_list_periods_returns_empty_list_initially(client: TestClient, auth_headers: Dict):
    """Listing periods for a new user returns an empty list."""
    resp = client.get(f"{BASE_URL}/", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_periods_returns_created_period(client: TestClient, auth_headers: Dict):
    """After creating a period it appears in the list."""
    create_period(client, auth_headers)
    resp = client.get(f"{BASE_URL}/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["period_name"] == VALID_PERIOD_PAYLOAD["period_name"]


def test_list_periods_returns_multiple_periods(client: TestClient, auth_headers: Dict):
    """Multiple created periods all appear in the list."""
    payloads = [
        {
            "period_name": "Period A",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "snapshot_date": "2026-01-31",
        },
        {
            "period_name": "Period B",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "snapshot_date": "2026-02-28",
        },
    ]
    for p in payloads:
        create_period(client, auth_headers, p)

    resp = client.get(f"{BASE_URL}/", headers=auth_headers)
    assert resp.status_code == 200
    names = {p["period_name"] for p in resp.json()}
    assert "Period A" in names
    assert "Period B" in names


def test_list_periods_isolation_between_users(
    client: TestClient,
    auth_headers: Dict,
    db,
):
    """Periods created by one user are NOT visible to another user."""
    from app.core.security import create_access_token, get_password_hash
    from app.models.user import User

    # Create a second user directly in the DB
    other_user = User(
        id=uuid.uuid4(),
        email=f"other-{uuid.uuid4()}@example.com",
        password_hash=get_password_hash("pass"),
        full_name="Other User",
        is_active=True,
    )
    db.add(other_user)
    db.commit()
    other_token = create_access_token(data={"sub": str(other_user.id)})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # First user creates a period
    create_period(client, auth_headers)

    # Second user should see no periods
    resp = client.get(f"{BASE_URL}/", headers=other_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_periods_no_auth(client: TestClient):
    """Listing periods without a token returns 401."""
    resp = client.get(f"{BASE_URL}/")
    assert resp.status_code == 401


# ===========================================================================
# GET /periods/{period_id}
# ===========================================================================


def test_get_period_by_id_success(client: TestClient, auth_headers: Dict):
    """Retrieving an existing period by ID returns 200 with correct data."""
    created = create_period(client, auth_headers)
    period_id = created["id"]

    resp = client.get(f"{BASE_URL}/{period_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == period_id
    assert data["period_name"] == VALID_PERIOD_PAYLOAD["period_name"]


def test_get_period_by_id_404(client: TestClient, auth_headers: Dict):
    """Requesting a non-existent period returns 404."""
    non_existent = str(uuid.uuid4())
    resp = client.get(f"{BASE_URL}/{non_existent}", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Period not found"


def test_get_period_by_id_no_auth(client: TestClient, auth_headers: Dict):
    """Requesting a period without a token returns 401."""
    created = create_period(client, auth_headers)
    resp = client.get(f"{BASE_URL}/{created['id']}")
    assert resp.status_code == 401


def test_get_period_wrong_user_returns_404(client: TestClient, auth_headers: Dict, db):
    """A period created by user A is not visible to user B (returns 404)."""
    from app.core.security import create_access_token, get_password_hash
    from app.models.user import User

    # Create a period as the first user
    created = create_period(client, auth_headers)

    # Create second user
    other_user = User(
        id=uuid.uuid4(),
        email=f"other2-{uuid.uuid4()}@example.com",
        password_hash=get_password_hash("pass"),
        full_name="Other User 2",
        is_active=True,
    )
    db.add(other_user)
    db.commit()
    other_token = create_access_token(data={"sub": str(other_user.id)})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    resp = client.get(f"{BASE_URL}/{created['id']}", headers=other_headers)
    assert resp.status_code == 404


# ===========================================================================
# PATCH /periods/{period_id}/status
# ===========================================================================


def test_update_period_status_to_finalized(client: TestClient, auth_headers: Dict):
    """Updating status to FINALIZED returns 200 with status=FINALIZED and finalized_at set."""
    created = create_period(client, auth_headers)
    period_id = created["id"]

    resp = client.patch(
        f"{BASE_URL}/{period_id}/status",
        json={"status": "FINALIZED"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "FINALIZED"
    assert data["finalized_at"] is not None


def test_update_period_status_to_archived(client: TestClient, auth_headers: Dict):
    """Updating status to ARCHIVED returns 200."""
    created = create_period(client, auth_headers)
    resp = client.patch(
        f"{BASE_URL}/{created['id']}/status",
        json={"status": "ARCHIVED"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ARCHIVED"


def test_update_period_status_to_draft(client: TestClient, auth_headers: Dict):
    """Updating status back to DRAFT returns 200."""
    created = create_period(client, auth_headers)
    resp = client.patch(
        f"{BASE_URL}/{created['id']}/status",
        json={"status": "DRAFT"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "DRAFT"


def test_update_period_status_invalid_value(client: TestClient, auth_headers: Dict):
    """Updating status with an invalid value returns 422."""
    created = create_period(client, auth_headers)
    resp = client.patch(
        f"{BASE_URL}/{created['id']}/status",
        json={"status": "INVALID_STATUS"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_update_period_status_404(client: TestClient, auth_headers: Dict):
    """Updating status of a non-existent period returns 404."""
    non_existent = str(uuid.uuid4())
    resp = client.patch(
        f"{BASE_URL}/{non_existent}/status",
        json={"status": "FINALIZED"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Period not found"


def test_update_period_status_no_auth(client: TestClient, auth_headers: Dict):
    """Updating period status without a token returns 401."""
    created = create_period(client, auth_headers)
    resp = client.patch(
        f"{BASE_URL}/{created['id']}/status",
        json={"status": "FINALIZED"},
    )
    assert resp.status_code == 401


# ===========================================================================
# DELETE /periods/{period_id}
# ===========================================================================


def test_delete_period_success(client: TestClient, auth_headers: Dict):
    """Deleting an existing period returns 200 with the deleted period's data."""
    created = create_period(client, auth_headers)
    period_id = created["id"]

    resp = client.delete(f"{BASE_URL}/{period_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == period_id
    assert data["period_name"] == VALID_PERIOD_PAYLOAD["period_name"]


def test_delete_period_is_gone_after_deletion(client: TestClient, auth_headers: Dict):
    """After deleting a period, trying to GET it returns 404."""
    created = create_period(client, auth_headers)
    period_id = created["id"]

    client.delete(f"{BASE_URL}/{period_id}", headers=auth_headers)

    resp = client.get(f"{BASE_URL}/{period_id}", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_period_removed_from_list(client: TestClient, auth_headers: Dict):
    """After deleting a period, it no longer appears in the list."""
    created = create_period(client, auth_headers)
    period_id = created["id"]

    client.delete(f"{BASE_URL}/{period_id}", headers=auth_headers)

    list_resp = client.get(f"{BASE_URL}/", headers=auth_headers)
    ids = [p["id"] for p in list_resp.json()]
    assert period_id not in ids


def test_delete_period_404(client: TestClient, auth_headers: Dict):
    """Deleting a non-existent period returns 404."""
    non_existent = str(uuid.uuid4())
    resp = client.delete(f"{BASE_URL}/{non_existent}", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Period not found"


def test_delete_period_no_auth(client: TestClient, auth_headers: Dict):
    """Deleting a period without a token returns 401."""
    created = create_period(client, auth_headers)
    resp = client.delete(f"{BASE_URL}/{created['id']}")
    assert resp.status_code == 401


def test_delete_period_wrong_user(client: TestClient, auth_headers: Dict, db):
    """User B cannot delete a period owned by user A."""
    from app.core.security import create_access_token, get_password_hash
    from app.models.user import User

    created = create_period(client, auth_headers)

    other_user = User(
        id=uuid.uuid4(),
        email=f"deltest-{uuid.uuid4()}@example.com",
        password_hash=get_password_hash("pass"),
        full_name="Delete Test User",
        is_active=True,
    )
    db.add(other_user)
    db.commit()
    other_token = create_access_token(data={"sub": str(other_user.id)})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    resp = client.delete(f"{BASE_URL}/{created['id']}", headers=other_headers)
    assert resp.status_code == 404

    # Original user should still see it
    resp2 = client.get(f"{BASE_URL}/{created['id']}", headers=auth_headers)
    assert resp2.status_code == 200


# ===========================================================================
# Response shape / field validation
# ===========================================================================


def test_period_response_has_all_required_fields(client: TestClient, auth_headers: Dict):
    """PeriodResponse contains all documented fields."""
    created = create_period(client, auth_headers)
    required_fields = {
        "id", "user_id", "period_name", "start_date", "end_date",
        "snapshot_date", "status", "created_at", "updated_at",
    }
    assert required_fields.issubset(created.keys())


def test_period_default_status_is_draft(client: TestClient, auth_headers: Dict):
    """Newly created period has status DRAFT."""
    created = create_period(client, auth_headers)
    assert created["status"] == "DRAFT"


def test_period_finalized_at_is_none_for_draft(client: TestClient, auth_headers: Dict):
    """finalized_at is None/null for a DRAFT period."""
    created = create_period(client, auth_headers)
    assert created.get("finalized_at") is None
