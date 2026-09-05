import re
from urllib.parse import urlsplit


def test_root_serves_semantic_frontend_shell(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "EduTrack AI" in response.text
    assert 'id="auth-view"' in response.text
    assert 'id="app-shell"' in response.text


def test_frontend_declares_the_interactive_learning_campus(client):
    response = client.get("/")

    assert 'id="learning-campus"' in response.text
    assert "/static/assets/learning-campus.png" in response.text
    assert "/static/vendor/phosphor/style.css" in response.text


def test_frontend_declares_classroom_integration_route_and_assets(client):
    html = client.get("/").text

    assert 'href="#integrations"' in html
    assert 'id="integrations-view"' in html
    assert 'id="classroom-integration"' in html
    assert "/static/css/integrations.css" in html
    assert client.get("/static/js/integrations.js").status_code == 200


def test_dashboard_offers_direct_classroom_sync_shortcut(client):
    html = client.get("/").text

    assert 'id="dashboard-classroom-sync"' in html
    assert 'href="#integrations"' in html
    assert "Sincronizar Classroom" in html


def test_learning_campus_assets_are_served(client):
    campus = client.get("/static/assets/learning-campus.png")
    agenda = client.get("/static/assets/agenda-clear.png")

    assert campus.status_code == 200
    assert campus.headers["content-type"] == "image/png"
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
