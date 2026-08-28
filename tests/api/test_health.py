def test_health_returns_ok(client):
    """Catches a missing or renamed public health endpoint."""
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
