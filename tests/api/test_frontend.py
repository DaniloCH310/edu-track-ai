def test_root_serves_semantic_frontend_shell(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "EduTrack AI" in response.text
    assert 'id="auth-view"' in response.text
    assert 'id="app-shell"' in response.text
