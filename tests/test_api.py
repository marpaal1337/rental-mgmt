from datetime import date

from fastapi.testclient import TestClient

from app.config import API_KEY

HEADERS = {"X-API-Key": API_KEY}


class TestAuth:
    def test_no_key_returns_403(self, client: TestClient):
        resp = client.get("/api/leases")
        assert resp.status_code == 403

    def test_invalid_key_returns_403(self, client: TestClient):
        resp = client.get("/api/leases", headers={"X-API-Key": "wrong"})
        assert resp.status_code == 403

    def test_valid_key_allows_access(self, client: TestClient):
        resp = client.get("/api/leases", headers=HEADERS)
        assert resp.status_code == 200

    def test_owners_needs_auth(self, client: TestClient):
        resp = client.get("/api/owners")
        assert resp.status_code == 403

    def test_tenants_needs_auth(self, client: TestClient):
        resp = client.get("/api/tenants")
        assert resp.status_code == 403

    def test_properties_needs_auth(self, client: TestClient):
        resp = client.get("/api/properties")
        assert resp.status_code == 403

    def test_units_needs_auth(self, client: TestClient):
        resp = client.get("/api/units")
        assert resp.status_code == 403

    def test_stats_needs_auth(self, client: TestClient):
        resp = client.get("/api/stats")
        assert resp.status_code == 403


class TestReferenceData:
    def test_owners_empty(self, client: TestClient):
        resp = client.get("/api/owners", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_tenants_empty(self, client: TestClient):
        resp = client.get("/api/tenants", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_properties_empty(self, client: TestClient):
        resp = client.get("/api/properties", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_units_empty(self, client: TestClient):
        resp = client.get("/api/units", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []


class TestStats:
    def test_stats_with_no_data(self, client: TestClient):
        resp = client.get("/api/stats", headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_leases"] == 0
        assert data["month_invoices"] == 0
        assert data["month_payments"] == 0
        assert data["year_expenses"] == 0


class TestLeases:
    def test_list_leases(self, client: TestClient):
        resp = client.get("/api/leases", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_lease_not_found(self, client: TestClient):
        resp = client.get("/api/leases/999", headers=HEADERS)
        assert resp.status_code == 404

    def test_create_and_update_lease(self, client: TestClient, refs: dict[str, int]):
        payload = {
            **refs,
            "start_date": "2024-01-01",
        }
        resp = client.post("/api/leases", json=payload, headers=HEADERS)
        assert resp.status_code == 201
        lease = resp.json()
        assert lease["unit_id"] == refs["unit_id"]
        lid = lease["id"]

        update = {"notes": "Updated notes"}
        resp = client.put(f"/api/leases/{lid}", json=update, headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["notes"] == "Updated notes"

    def test_update_nonexistent_lease(self, client: TestClient):
        resp = client.put("/api/leases/999", json={"notes": "test"}, headers=HEADERS)
        assert resp.status_code == 404

    def test_update_lease_inactive(self, client: TestClient, refs: dict[str, int]):
        payload = {
            **refs,
            "start_date": "2024-01-01",
        }
        resp = client.post("/api/leases", json=payload, headers=HEADERS)
        lid = resp.json()["id"]

        resp = client.put(
            f"/api/leases/{lid}",
            json={"is_active": False},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False


class TestInvoices:
    def _create_lease_with_fiscal_data(
        self, client: TestClient, refs: dict[str, int], *, exempt: bool = True
    ) -> dict:
        lease = client.post(
            "/api/leases",
            json={**refs, "start_date": "2024-01-01"},
            headers=HEADERS,
        ).json()
        client.post(
            f"/api/leases/{lease['id']}/rent-conditions",
            json={"start_date": "2024-01-01", "monthly_rent": "1000.00"},
            headers=HEADERS,
        )
        client.put(
            f"/api/leases/{lease['id']}/tax-profile",
            json={
                "vat_rate": "0" if exempt else "21.00",
                "irpf_rate": "0",
                "vat_exempt": exempt,
                "withholding_applies": False,
            },
            headers=HEADERS,
        )
        return lease

    def test_generate_without_data_returns_empty(self, client: TestClient):
        resp = client.post(
            "/api/invoices/generate",
            json={"period": "2024-06"},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        assert resp.json() == []

    def test_generate_assigns_legal_number_and_due_date(
        self, client: TestClient, refs: dict[str, int]
    ):
        self._create_lease_with_fiscal_data(client, refs)
        resp = client.post(
            "/api/invoices/generate",
            json={"period": "2024-06"},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        invoice = resp.json()[0]
        year = date.today().year
        assert invoice["number"] == f"A-{year}-0001"
        assert invoice["series"] == "A"
        assert invoice["fiscal_year"] == year
        assert invoice["due_date"] is not None
        assert invoice["sequence"] == 1

    def test_rectify_creates_negative_invoice(
        self, client: TestClient, refs: dict[str, int]
    ):
        self._create_lease_with_fiscal_data(client, refs)
        invoice = client.post(
            "/api/invoices/generate",
            json={"period": "2024-06"},
            headers=HEADERS,
        ).json()[0]

        resp = client.post(
            f"/api/invoices/{invoice['id']}/rectify",
            json={"reason": "Importe incorrecto"},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        rectification = resp.json()
        year = date.today().year
        assert rectification["number"] == f"R-{year}-0001"
        assert rectification["corrected_invoice_id"] == invoice["id"]
        assert float(rectification["total"]) == -float(invoice["total"])
        assert rectification["lines"][0]["base_amount"].startswith("-")

        second = client.post(
            f"/api/invoices/{invoice['id']}/rectify",
            json={"reason": "Otra vez"},
            headers=HEADERS,
        )
        assert second.status_code == 400

        regenerated = client.post(
            "/api/invoices/generate",
            json={"period": "2024-06"},
            headers=HEADERS,
        ).json()
        assert regenerated == []

    def test_rectify_not_found(self, client: TestClient):
        resp = client.post(
            "/api/invoices/999/rectify",
            json={"reason": "Motivo"},
            headers=HEADERS,
        )
        assert resp.status_code == 404

    def test_rectify_requires_reason(self, client: TestClient, refs: dict[str, int]):
        self._create_lease_with_fiscal_data(client, refs)
        invoice = client.post(
            "/api/invoices/generate",
            json={"period": "2024-06"},
            headers=HEADERS,
        ).json()[0]

        resp = client.post(
            f"/api/invoices/{invoice['id']}/rectify",
            json={"reason": ""},
            headers=HEADERS,
        )
        assert resp.status_code == 422


class TestExpenses:
    def test_categories(self, client: TestClient):
        resp = client.get("/api/expenses/categories", headers=HEADERS)
        assert resp.status_code == 200
        assert "categories" in resp.json()
        cats = resp.json()["categories"]
        assert "community" in cats

    def test_register_no_property_returns_error(self, client: TestClient):
        resp = client.post(
            "/api/expenses",
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
            "/api/expenses/999",
            json={"supplier": "Test"},
            headers=HEADERS,
        )
        assert resp.status_code == 404


class TestPayments:
    def test_update_nonexistent_payment(self, client: TestClient):
        resp = client.put(
            "/api/payments/999",
            json={"method": "efectivo"},
            headers=HEADERS,
        )
        assert resp.status_code == 404

    def test_list_payments(self, client: TestClient):
        resp = client.get("/api/payments", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestReconciliation:
    def test_unmatched_returns_empty_list(self, client: TestClient):
        resp = client.get("/api/reconciliation/unmatched", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_movements_empty(self, client: TestClient):
        resp = client.get("/api/reconciliation/movements", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []


class TestOwners:
    def test_create_and_get(self, client: TestClient):
        resp = client.post("/api/owners", json={
            "name": "Test Owner", "document_type": "DNI",
            "document_number": "12345678A", "email": "o@t.com",
            "phone": "+34 600 000 000",
        }, headers=HEADERS)
        assert resp.status_code == 201
        oid = resp.json()["id"]

        resp = client.get(f"/api/owners/{oid}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Owner"

    def test_get_not_found(self, client: TestClient):
        assert client.get("/api/owners/999", headers=HEADERS).status_code == 404

    def test_update(self, client: TestClient):
        resp = client.post("/api/owners", json={
            "name": "Old Name", "document_type": "DNI",
            "document_number": "87654321B", "email": "old@t.com",
            "phone": "+34 611 111 111",
        }, headers=HEADERS)
        oid = resp.json()["id"]

        resp = client.put(f"/api/owners/{oid}", json={"name": "New Name"}, headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_update_not_found(self, client: TestClient):
        resp = client.put("/api/owners/999", json={"name": "X"}, headers=HEADERS)
        assert resp.status_code == 404

    def test_list(self, client: TestClient):
        resp = client.get("/api/owners", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestProperties:
    def test_create_and_get(self, client: TestClient):
        resp = client.post("/api/owners", json={
            "name": "Prop Owner", "document_type": "DNI",
            "document_number": "11111111C", "email": "po@t.com",
            "phone": "+34 622 222 222",
        }, headers=HEADERS)
        oid = resp.json()["id"]

        resp = client.post("/api/properties", json={
            "name": "Test Property", "address": "Calle 1", "city": "Madrid",
            "province": "Madrid", "zip_code": "28001", "owner_id": oid,
        }, headers=HEADERS)
        assert resp.status_code == 201
        pid = resp.json()["id"]

        resp = client.get(f"/api/properties/{pid}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Property"

    def test_get_not_found(self, client: TestClient):
        assert client.get("/api/properties/999", headers=HEADERS).status_code == 404

    def test_update(self, client: TestClient):
        resp = client.post("/api/owners", json={
            "name": "P2 Owner", "document_type": "DNI",
            "document_number": "22222222D", "email": "p2@t.com",
            "phone": "+34 633 333 333",
        }, headers=HEADERS)
        oid = resp.json()["id"]

        resp = client.post("/api/properties", json={
            "name": "Old Prop", "address": "Calle 2", "city": "Madrid",
            "province": "Madrid", "zip_code": "28001", "owner_id": oid,
        }, headers=HEADERS)
        pid = resp.json()["id"]

        resp = client.put(f"/api/properties/{pid}", json={"name": "New Prop"}, headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Prop"

    def test_update_not_found(self, client: TestClient):
        resp = client.put("/api/properties/999", json={"name": "X"}, headers=HEADERS)
        assert resp.status_code == 404

    def test_list(self, client: TestClient):
        resp = client.get("/api/properties", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestUnits:
    def test_create_and_get(self, client: TestClient):
        resp = client.post("/api/owners", json={
            "name": "U Owner", "document_type": "DNI",
            "document_number": "33333333E", "email": "uo@t.com",
            "phone": "+34 644 444 444",
        }, headers=HEADERS)
        oid = resp.json()["id"]

        resp = client.post("/api/properties", json={
            "name": "U Prop", "address": "Calle U", "city": "Madrid",
            "province": "Madrid", "zip_code": "28001", "owner_id": oid,
        }, headers=HEADERS)
        pid = resp.json()["id"]

        resp = client.post("/api/units", json={
            "property_id": pid, "name": "Unit 1", "unit_type": "vivienda",
        }, headers=HEADERS)
        assert resp.status_code == 201
        uid = resp.json()["id"]

        resp = client.get(f"/api/units/{uid}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Unit 1"

    def test_get_not_found(self, client: TestClient):
        assert client.get("/api/units/999", headers=HEADERS).status_code == 404

    def test_update(self, client: TestClient):
        resp = client.post("/api/owners", json={
            "name": "U2 Owner", "document_type": "DNI",
            "document_number": "44444444F", "email": "u2o@t.com",
            "phone": "+34 655 555 555",
        }, headers=HEADERS)
        oid = resp.json()["id"]

        resp = client.post("/api/properties", json={
            "name": "U2 Prop", "address": "Calle U2", "city": "Madrid",
            "province": "Madrid", "zip_code": "28001", "owner_id": oid,
        }, headers=HEADERS)
        pid = resp.json()["id"]

        resp = client.post("/api/units", json={
            "property_id": pid, "name": "Old Unit", "unit_type": "vivienda",
        }, headers=HEADERS)
        uid = resp.json()["id"]

        resp = client.put(f"/api/units/{uid}", json={"name": "New Unit"}, headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Unit"

    def test_update_not_found(self, client: TestClient):
        resp = client.put("/api/units/999", json={"name": "X"}, headers=HEADERS)
        assert resp.status_code == 404

    def test_list(self, client: TestClient):
        resp = client.get("/api/units", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestTenants:
    def test_create_and_get(self, client: TestClient):
        resp = client.post("/api/tenants", json={
            "name": "Test Tenant", "document_type": "DNI",
            "document_number": "55555555G", "email": "t@t.com",
            "phone": "+34 666 666 666",
        }, headers=HEADERS)
        assert resp.status_code == 201
        tid = resp.json()["id"]

        resp = client.get(f"/api/tenants/{tid}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Tenant"

    def test_get_not_found(self, client: TestClient):
        assert client.get("/api/tenants/999", headers=HEADERS).status_code == 404

    def test_update(self, client: TestClient):
        resp = client.post("/api/tenants", json={
            "name": "Old Tenant", "document_type": "NIE",
            "document_number": "Y6666666H", "email": "old@t.com",
            "phone": "+34 677 777 777",
        }, headers=HEADERS)
        tid = resp.json()["id"]

        resp = client.put(f"/api/tenants/{tid}", json={"name": "New Tenant"}, headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Tenant"

    def test_update_not_found(self, client: TestClient):
        resp = client.put("/api/tenants/999", json={"name": "X"}, headers=HEADERS)
        assert resp.status_code == 404

    def test_list(self, client: TestClient):
        resp = client.get("/api/tenants", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestRentConditions:
    def test_create_and_list(self, client: TestClient, refs: dict[str, int]):
        resp = client.post("/api/leases", json={
            **refs, "start_date": "2024-01-01",
        }, headers=HEADERS)
        lid = resp.json()["id"]

        resp = client.post(f"/api/leases/{lid}/rent-conditions", json={
            "start_date": "2024-01-01", "monthly_rent": "950.00",
        }, headers=HEADERS)
        assert resp.status_code == 201
        assert resp.json()["monthly_rent"] == "950.00"

        resp = client.get(f"/api/leases/{lid}/rent-conditions", headers=HEADERS)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_on_nonexistent_lease(self, client: TestClient):
        resp = client.get("/api/leases/999/rent-conditions", headers=HEADERS)
        assert resp.status_code == 404


class TestTaxProfile:
    def test_upsert_and_get(self, client: TestClient, refs: dict[str, int]):
        resp = client.post("/api/leases", json={
            **refs, "start_date": "2024-01-01",
        }, headers=HEADERS)
        lid = resp.json()["id"]

        resp = client.put(f"/api/leases/{lid}/tax-profile", json={
            "vat_rate": "10.00", "irpf_rate": "19.00",
        }, headers=HEADERS)
        assert resp.status_code == 200

        resp = client.get(f"/api/leases/{lid}/tax-profile", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["vat_rate"] == "10.00"

    def test_get_not_found(self, client: TestClient):
        resp = client.get("/api/leases/999/tax-profile", headers=HEADERS)
        assert resp.status_code == 404


class TestDeposit:
    def test_upsert_and_get(self, client: TestClient, refs: dict[str, int]):
        resp = client.post("/api/leases", json={
            **refs, "start_date": "2024-01-01",
        }, headers=HEADERS)
        lid = resp.json()["id"]

        resp = client.put(f"/api/leases/{lid}/deposit", json={
            "amount": "950.00", "deposit_date": "2024-01-01", "agency": "IVIMA",
        }, headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["amount"] == "950.00"

        resp = client.get(f"/api/leases/{lid}/deposit", headers=HEADERS)
        assert resp.status_code == 200

    def test_get_not_found(self, client: TestClient):
        resp = client.get("/api/leases/999/deposit", headers=HEADERS)
        assert resp.status_code == 404


class TestIndexUpdates:
    def test_list_empty_and_apply(self, client: TestClient, refs: dict[str, int]):
        resp = client.post("/api/leases", json={
            **refs, "start_date": "2024-01-01",
        }, headers=HEADERS)
        lid = resp.json()["id"]

        resp = client.get(f"/api/leases/{lid}/index-updates", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json() == []

        resp = client.post(f"/api/leases/{lid}/rent-conditions", json={
            "start_date": "2024-01-01", "monthly_rent": "950.00",
        }, headers=HEADERS)

        resp = client.post(f"/api/leases/{lid}/apply-index", json={
            "index_rate": "0.03", "application_date": "2025-01-01",
        }, headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "rent_condition" in data
        assert "index_update" in data

        resp = client.get(f"/api/leases/{lid}/index-updates", headers=HEADERS)
        assert len(resp.json()) == 1

    def test_apply_no_rent_condition(self, client: TestClient, refs: dict[str, int]):
        resp = client.post("/api/leases", json={
            **refs, "start_date": "2024-01-01",
        }, headers=HEADERS)
        lid = resp.json()["id"]

        resp = client.post(f"/api/leases/{lid}/apply-index", json={
            "index_rate": "0.03", "application_date": "2025-01-01",
        }, headers=HEADERS)
        assert resp.status_code == 404


class TestExpenseSummary:
    def test_summary_no_property(self, client: TestClient):
        resp = client.get("/api/expenses/summary", params={
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
