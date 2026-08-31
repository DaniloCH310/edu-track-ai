import re
from urllib.parse import urlsplit


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


def test_frontend_prevents_html_and_javascript_from_becoming_stale(client):
    html = client.get("/")
    javascript = client.get("/static/js/app.js")

    assert html.headers["cache-control"] == "no-store"
    assert javascript.headers["cache-control"] == "no-store"


def test_frontend_uses_versioned_password_toggle_assets(client):
    html = client.get("/").text
    stylesheet = re.search(r'href="(/static/css/app\.css[^"]*)"', html)
    entrypoint = re.search(r'src="(/static/js/app\.js[^"]*)"', html)

    assert stylesheet is not None
    assert entrypoint is not None
    assert urlsplit(stylesheet.group(1)).query
    assert urlsplit(entrypoint.group(1)).query

    javascript = client.get(entrypoint.group(1)).text
    ui_module = re.search(r'from "(\./ui\.js[^"]*)"', javascript)

    assert ui_module is not None
    assert urlsplit(ui_module.group(1)).query
