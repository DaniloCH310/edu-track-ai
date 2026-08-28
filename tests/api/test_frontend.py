def test_root_serves_semantic_frontend_shell(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "EduTrack AI" in response.text
    assert 'id="auth-view"' in response.text
    assert 'id="app-shell"' in response.text


def test_frontend_declares_the_interactive_learning_journey(client):
    response = client.get("/")

    assert 'id="learning-journey"' in response.text
    assert "/static/assets/learning-islands.png" in response.text
    assert "/static/vendor/phosphor/style.css" in response.text


def test_learning_journey_assets_are_served(client):
    islands = client.get("/static/assets/learning-islands.png")
    agenda = client.get("/static/assets/agenda-clear.png")

    assert islands.status_code == 200
    assert islands.headers["content-type"] == "image/png"
    assert agenda.status_code == 200
    assert agenda.headers["content-type"] == "image/png"
