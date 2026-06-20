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


class TestOwners:
    def test_create_and_get(self, client: TestClient):
        resp = client.post("/owners", json={
            "name": "Test Owner", "document_type": "DNI",
            "document_number": "12345678A", "email": "o@t.com",
            "phone": "+34 600 000 000",
        }, headers=HEADERS)
        assert resp.status_code == 201
        oid = resp.json()["id"]

        resp = client.get(f"/owners/{oid}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Owner"

    def test_get_not_found(self, client: TestClient):
        assert client.get("/owners/999", headers=HEADERS).status_code == 404

    def test_update(self, client: TestClient):
        resp = client.post("/owners", json={
            "name": "Old Name", "document_type": "DNI",
            "document_number": "87654321B", "email": "old@t.com",
            "phone": "+34 611 111 111",
        }, headers=HEADERS)
        oid = resp.json()["id"]

        resp = client.put(f"/owners/{oid}", json={"name": "New Name"}, headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_update_not_found(self, client: TestClient):
        resp = client.put("/owners/999", json={"name": "X"}, headers=HEADERS)
        assert resp.status_code == 404

    def test_list(self, client: TestClient):
        resp = client.get("/owners", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestProperties:
    def test_create_and_get(self, client: TestClient):
        resp = client.post("/owners", json={
            "name": "Prop Owner", "document_type": "DNI",
            "document_number": "11111111C", "email": "po@t.com",
            "phone": "+34 622 222 222",
        }, headers=HEADERS)
        oid = resp.json()["id"]

        resp = client.post("/properties", json={
            "name": "Test Property", "address": "Calle 1", "city": "Madrid",
            "province": "Madrid", "zip_code": "28001", "owner_id": oid,
        }, headers=HEADERS)
        assert resp.status_code == 201
        pid = resp.json()["id"]

        resp = client.get(f"/properties/{pid}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Property"

    def test_get_not_found(self, client: TestClient):
        assert client.get("/properties/999", headers=HEADERS).status_code == 404

    def test_update(self, client: TestClient):
        resp = client.post("/owners", json={
            "name": "P2 Owner", "document_type": "DNI",
            "document_number": "22222222D", "email": "p2@t.com",
            "phone": "+34 633 333 333",
        }, headers=HEADERS)
        oid = resp.json()["id"]

        resp = client.post("/properties", json={
            "name": "Old Prop", "address": "Calle 2", "city": "Madrid",
            "province": "Madrid", "zip_code": "28001", "owner_id": oid,
        }, headers=HEADERS)
        pid = resp.json()["id"]

        resp = client.put(f"/properties/{pid}", json={"name": "New Prop"}, headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Prop"

    def test_update_not_found(self, client: TestClient):
        resp = client.put("/properties/999", json={"name": "X"}, headers=HEADERS)
        assert resp.status_code == 404

    def test_list(self, client: TestClient):
        resp = client.get("/properties", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestUnits:
    def test_create_and_get(self, client: TestClient):
        resp = client.post("/owners", json={
            "name": "U Owner", "document_type": "DNI",
            "document_number": "33333333E", "email": "uo@t.com",
            "phone": "+34 644 444 444",
        }, headers=HEADERS)
        oid = resp.json()["id"]

        resp = client.post("/properties", json={
            "name": "U Prop", "address": "Calle U", "city": "Madrid",
            "province": "Madrid", "zip_code": "28001", "owner_id": oid,
        }, headers=HEADERS)
        pid = resp.json()["id"]

        resp = client.post("/units", json={
            "property_id": pid, "name": "Unit 1", "unit_type": "vivienda",
        }, headers=HEADERS)
        assert resp.status_code == 201
        uid = resp.json()["id"]

        resp = client.get(f"/units/{uid}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Unit 1"

    def test_get_not_found(self, client: TestClient):
        assert client.get("/units/999", headers=HEADERS).status_code == 404

    def test_update(self, client: TestClient):
        resp = client.post("/owners", json={
            "name": "U2 Owner", "document_type": "DNI",
            "document_number": "44444444F", "email": "u2o@t.com",
            "phone": "+34 655 555 555",
        }, headers=HEADERS)
        oid = resp.json()["id"]

        resp = client.post("/properties", json={
            "name": "U2 Prop", "address": "Calle U2", "city": "Madrid",
            "province": "Madrid", "zip_code": "28001", "owner_id": oid,
        }, headers=HEADERS)
        pid = resp.json()["id"]

        resp = client.post("/units", json={
            "property_id": pid, "name": "Old Unit", "unit_type": "vivienda",
        }, headers=HEADERS)
        uid = resp.json()["id"]

        resp = client.put(f"/units/{uid}", json={"name": "New Unit"}, headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Unit"

    def test_update_not_found(self, client: TestClient):
        resp = client.put("/units/999", json={"name": "X"}, headers=HEADERS)
        assert resp.status_code == 404

    def test_list(self, client: TestClient):
        resp = client.get("/units", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestTenants:
    def test_create_and_get(self, client: TestClient):
        resp = client.post("/tenants", json={
            "name": "Test Tenant", "document_type": "DNI",
            "document_number": "55555555G", "email": "t@t.com",
            "phone": "+34 666 666 666",
        }, headers=HEADERS)
        assert resp.status_code == 201
        tid = resp.json()["id"]

        resp = client.get(f"/tenants/{tid}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Tenant"

    def test_get_not_found(self, client: TestClient):
        assert client.get("/tenants/999", headers=HEADERS).status_code == 404

    def test_update(self, client: TestClient):
        resp = client.post("/tenants", json={
            "name": "Old Tenant", "document_type": "NIE",
            "document_number": "Y6666666H", "email": "old@t.com",
            "phone": "+34 677 777 777",
        }, headers=HEADERS)
        tid = resp.json()["id"]

        resp = client.put(f"/tenants/{tid}", json={"name": "New Tenant"}, headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Tenant"

    def test_update_not_found(self, client: TestClient):
        resp = client.put("/tenants/999", json={"name": "X"}, headers=HEADERS)
        assert resp.status_code == 404

    def test_list(self, client: TestClient):
        resp = client.get("/tenants", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestRentConditions:
    def test_create_and_list(self, client: TestClient):
        resp = client.post("/leases", json={
            "unit_id": 1, "tenant_id": 1, "owner_id": 1,
            "start_date": "2024-01-01",
        }, headers=HEADERS)
        lid = resp.json()["id"]

        resp = client.post(f"/leases/{lid}/rent-conditions", json={
            "start_date": "2024-01-01", "monthly_rent": "950.00",
        }, headers=HEADERS)
        assert resp.status_code == 201
        assert resp.json()["monthly_rent"] == "950.00"

        resp = client.get(f"/leases/{lid}/rent-conditions", headers=HEADERS)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_on_nonexistent_lease(self, client: TestClient):
        resp = client.get("/leases/999/rent-conditions", headers=HEADERS)
        assert resp.status_code == 404


class TestTaxProfile:
    def test_upsert_and_get(self, client: TestClient):
        resp = client.post("/leases", json={
            "unit_id": 1, "tenant_id": 1, "owner_id": 1,
            "start_date": "2024-01-01",
        }, headers=HEADERS)
        lid = resp.json()["id"]

        resp = client.put(f"/leases/{lid}/tax-profile", json={
            "vat_rate": "10.00", "irpf_rate": "19.00",
        }, headers=HEADERS)
        assert resp.status_code == 200

        resp = client.get(f"/leases/{lid}/tax-profile", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["vat_rate"] == "10.00"

    def test_get_not_found(self, client: TestClient):
        resp = client.get("/leases/999/tax-profile", headers=HEADERS)
        assert resp.status_code == 404


class TestDeposit:
    def test_upsert_and_get(self, client: TestClient):
        resp = client.post("/leases", json={
            "unit_id": 1, "tenant_id": 1, "owner_id": 1,
            "start_date": "2024-01-01",
        }, headers=HEADERS)
        lid = resp.json()["id"]

        resp = client.put(f"/leases/{lid}/deposit", json={
            "amount": "950.00", "deposit_date": "2024-01-01", "agency": "IVIMA",
        }, headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["amount"] == "950.00"

        resp = client.get(f"/leases/{lid}/deposit", headers=HEADERS)
        assert resp.status_code == 200

    def test_get_not_found(self, client: TestClient):
        resp = client.get("/leases/999/deposit", headers=HEADERS)
        assert resp.status_code == 404


class TestIndexUpdates:
    def test_list_empty_and_apply(self, client: TestClient):
        resp = client.post("/leases", json={
            "unit_id": 1, "tenant_id": 1, "owner_id": 1,
            "start_date": "2024-01-01",
        }, headers=HEADERS)
        lid = resp.json()["id"]

        resp = client.get(f"/leases/{lid}/index-updates", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []

        resp = client.post(f"/leases/{lid}/rent-conditions", json={
            "start_date": "2024-01-01", "monthly_rent": "950.00",
        }, headers=HEADERS)

        resp = client.post(f"/leases/{lid}/apply-index", json={
            "index_rate": "0.03", "application_date": "2025-01-01",
        }, headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "rent_condition" in data
        assert "index_update" in data

        resp = client.get(f"/leases/{lid}/index-updates", headers=HEADERS)
        assert len(resp.json()) == 1

    def test_apply_no_rent_condition(self, client: TestClient):
        resp = client.post("/leases", json={
            "unit_id": 1, "tenant_id": 1, "owner_id": 1,
            "start_date": "2024-01-01",
        }, headers=HEADERS)
        lid = resp.json()["id"]

        resp = client.post(f"/leases/{lid}/apply-index", json={
            "index_rate": "0.03", "application_date": "2025-01-01",
        }, headers=HEADERS)
        assert resp.status_code == 404


class TestExpenseSummary:
    def test_summary_no_property(self, client: TestClient):
        resp = client.get("/expenses/summary", params={
            "property_id": 999, "year": 2026,
        }, headers=HEADERS)
        assert resp.status_code == 404


class TestHealth:
    def test_health(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_root(self, client: TestClient):
        resp = client.get("/")
        assert resp.status_code == 200
        ct = resp.headers.get("content-type", "")
        if "html" in ct:
            assert "<html" in resp.text.lower()
        else:
            assert "message" in resp.json()
