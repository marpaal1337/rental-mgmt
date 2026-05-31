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

    def test_owners_needs_auth(self, client: TestClient):
        resp = client.get("/owners")
        assert resp.status_code == 403

    def test_tenants_needs_auth(self, client: TestClient):
        resp = client.get("/tenants")
        assert resp.status_code == 403

    def test_properties_needs_auth(self, client: TestClient):
        resp = client.get("/properties")
        assert resp.status_code == 403

    def test_units_needs_auth(self, client: TestClient):
        resp = client.get("/units")
        assert resp.status_code == 403

    def test_stats_needs_auth(self, client: TestClient):
        resp = client.get("/stats")
        assert resp.status_code == 403


class TestReferenceData:
    def test_owners_empty(self, client: TestClient):
        resp = client.get("/owners", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_tenants_empty(self, client: TestClient):
        resp = client.get("/tenants", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_properties_empty(self, client: TestClient):
        resp = client.get("/properties", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_units_empty(self, client: TestClient):
        resp = client.get("/units", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []


class TestStats:
    def test_stats_with_no_data(self, client: TestClient):
        resp = client.get("/stats", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_leases"] == 0
        assert data["month_invoices"] == 0
        assert data["month_payments"] == 0
        assert data["year_expenses"] == 0


class TestLeases:
    def test_list_leases(self, client: TestClient):
        resp = client.get("/leases", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_lease_not_found(self, client: TestClient):
        resp = client.get("/leases/999", headers=HEADERS)
        assert resp.status_code == 404

    def test_create_and_update_lease(self, client: TestClient):
        payload = {
            "unit_id": 1,
            "tenant_id": 1,
            "owner_id": 1,
            "start_date": "2024-01-01",
        }
        resp = client.post("/leases", json=payload, headers=HEADERS)
        assert resp.status_code == 201
        lease = resp.json()
        assert lease["unit_id"] == 1
        lid = lease["id"]

        update = {"notes": "Updated notes"}
        resp = client.put(f"/leases/{lid}", json=update, headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["notes"] == "Updated notes"

    def test_update_nonexistent_lease(self, client: TestClient):
        resp = client.put("/leases/999", json={"notes": "test"}, headers=HEADERS)
        assert resp.status_code == 404

    def test_update_lease_inactive(self, client: TestClient):
        payload = {
            "unit_id": 1,
            "tenant_id": 1,
            "owner_id": 1,
            "start_date": "2024-01-01",
        }
        resp = client.post("/leases", json=payload, headers=HEADERS)
        lid = resp.json()["id"]

        resp = client.put(
            f"/leases/{lid}",
            json={"is_active": False},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False


class TestInvoices:
    def test_generate_without_data_returns_empty(self, client: TestClient):
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

    def test_register_no_property_returns_error(self, client: TestClient):
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

    def test_update_nonexistent_expense(self, client: TestClient):
        resp = client.put(
            "/expenses/999",
            json={"supplier": "Test"},
            headers=HEADERS,
        )
        assert resp.status_code == 404


class TestPayments:
    def test_update_nonexistent_payment(self, client: TestClient):
        resp = client.put(
            "/payments/999",
            json={"method": "efectivo"},
            headers=HEADERS,
        )
        assert resp.status_code == 404

    def test_list_payments(self, client: TestClient):
        resp = client.get("/payments", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestReconciliation:
    def test_unmatched_returns_empty_list(self, client: TestClient):
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
