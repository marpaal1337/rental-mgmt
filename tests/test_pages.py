class TestPages:
    def test_dashboard(self, client):
        resp = client.get("/app/")
        assert resp.status_code == 200
        assert "Dashboard" in resp.text

    def test_leases_page(self, client):
        resp = client.get("/app/leases")
        assert resp.status_code == 200
        assert "Contratos" in resp.text
