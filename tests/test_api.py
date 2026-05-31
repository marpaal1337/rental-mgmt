from fastapi.testclient import TestClient

from app.config import API_KEY

HEADERS = {"X-API-Key": API_KEY}


class TestAuth:
    def test_no_key_returns_403(self, client: TestClient):
        resp = client.get("/leases")
        assert resp.status_code == 403

    def test_invalid_key_returns_403(self, client: TestClient):
        resp = client.get("/leases", headers={"X-API-Key": "wrong"})
        assert resp.status_code == 403

    def test_valid_key_allows_access(self, client: TestClient):
        resp = client.get("/leases", headers=HEADERS)
        assert resp.status_code == 200


class TestLeases:
    def test_list_leases(self, client: TestClient):
        resp = client.get("/leases", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_lease_not_found(self, client: TestClient):
        resp = client.get("/leases/999", headers=HEADERS)
        assert resp.status_code == 404


class TestInvoices:
    def test_generate_without_data_returns_empty(
        self, client: TestClient
    ):
        resp = client.post(
            "/invoices/generate",
            json={"period": "2024-06"},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        assert resp.json() == []


class TestExpenses:
    def test_categories(self, client: TestClient):
        resp = client.get("/expenses/categories", headers=HEADERS)
        assert resp.status_code == 200
        assert "categories" in resp.json()
        cats = resp.json()["categories"]
        assert "community" in cats

    def test_register_no_property_returns_error(
        self, client: TestClient
    ):
        resp = client.post(
            "/expenses",
            json={
                "property_id": 999,
                "category": "community",
                "amount": "85.50",
                "expense_date": "2024-06-01",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 400


class TestReconciliation:
    def test_unmatched_returns_empty_list(
        self, client: TestClient
    ):
        resp = client.get("/reconciliation/unmatched", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_movements_empty(self, client: TestClient):
        resp = client.get("/reconciliation/movements", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []


class TestHealth:
    def test_health(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_root(self, client: TestClient):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "message" in resp.json()
