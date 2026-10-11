import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from main import app

smoke_client = TestClient(app)

VALID_SALE = {
    "transaction_id": "TXN-TEST-001",
    "sale_date": "2026-10-08",
    "city": "Nairobi",
    "branch": "CBD",
    "category": "Dresses",
    "product": "Floral Midi Dress",
    "quantity": 2,
    "unit_price_ksh": 3500,
    "payment_method": "M-Pesa",
}
import pytest

def test_health():
    response = smoke_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_sale_returns_201(client):
    response = client.post("/sales", json=VALID_SALE)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "saved"
    assert body["transaction_id"] == "TXN-TEST-001"
    assert body["id"] == 1


def test_created_sale_is_stored(client):
    client.post("/sales", json=VALID_SALE)
    response = client.get("/sales")
    assert response.status_code == 200
    sales = response.json()
    assert len(sales) == 1
    assert sales[0]["product"] == "Floral Midi Dress"


@pytest.mark.parametrize(
    "field, bad_value",
    [
        ("quantity", -5),
        ("quantity", 0),
        ("quantity", "banana"),
        ("unit_price_ksh", -100),
        ("unit_price_ksh", 0),
        ("payment_method", "Bitcoin"),
        ("sale_date", "not-a-date"),
    ],
)
def test_invalid_field_returns_422(client, field, bad_value):
    payload = {**VALID_SALE, field: bad_value}
    response = client.post("/sales", json=payload)
    assert response.status_code == 422
    error_fields = [err["loc"][-1] for err in response.json()["detail"]]
    assert field in error_fields


def test_missing_field_returns_422(client):
    payload = {k: v for k, v in VALID_SALE.items() if k != "transaction_id"}
    response = client.post("/sales", json=payload)
    assert response.status_code == 422
    error_fields = [err["loc"][-1] for err in response.json()["detail"]]
    assert "transaction_id" in error_fields


def test_rejected_sale_is_not_stored(client):
    client.post("/sales", json={**VALID_SALE, "quantity": -5})
    response = client.get("/sales")
    assert response.json() == []

def test_duplicate_transaction_id_returns_409(client):
    first = client.post("/sales", json=VALID_SALE)
    assert first.status_code == 201

    second = client.post("/sales", json=VALID_SALE)
    assert second.status_code == 409
    assert "TXN-TEST-001" in second.json()["detail"]

    stored = client.get("/sales").json()
    assert len(stored) == 1

def test_database_failure_returns_503_and_retry_succeeds(client, monkeypatch):
    async def failing_commit(self):
        raise OperationalError("COMMIT", {}, Exception("database is locked"))

    monkeypatch.setattr(AsyncSession, "commit", failing_commit)

    response = client.post("/sales", json=VALID_SALE)
    assert response.status_code == 503
    assert "locked" not in response.text
    assert client.get("/sales").json() == []

    monkeypatch.undo()

    retry = client.post("/sales", json=VALID_SALE)
    assert retry.status_code == 201