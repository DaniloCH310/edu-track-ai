import socket
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import pytest
import uvicorn
from playwright.sync_api import expect, sync_playwright

ARTIFACTS = Path("tmp/ui")


@dataclass
class LiveServer:
    url: str


@pytest.fixture(scope="session")
def live_server():
    from app.main import app

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    if not server.started:
        raise RuntimeError("O servidor E2E não iniciou.")
    yield LiveServer(f"http://127.0.0.1:{port}")
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture
def page(database_cleaner):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            headless=True,
        )
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        yield page
        browser.close()


def test_user_can_register_logout_and_login(page, live_server):
    page.goto(live_server.url)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=ARTIFACTS / "auth-desktop.png", full_page=True)
    page.get_by_role("tab", name="Criar conta").click()
    register = page.locator("#register-form")
    register.get_by_label("Nome").fill("Ana Estudante")
    register.get_by_label("E-mail").fill("ana@example.com")
    register.get_by_label("Senha").fill("Senha-Forte-123")
    register.get_by_role("button", name="Cadastrar").click()
    expect(page.get_by_role("heading", name="Olá, Ana")).to_be_visible()

    page.get_by_role("button", name="Sair").click()
    expect(page.get_by_role("heading", name="Bem-vindo de volta")).to_be_visible()
    login = page.locator("#login-form")
    login.get_by_label("E-mail").fill("ana@example.com")
    login.get_by_label("Senha").fill("Senha-Forte-123")
    login.get_by_role("button", name="Entrar", exact=True).click()
    expect(page.get_by_role("heading", name="Olá, Ana")).to_be_visible()


def test_mobile_auth_has_no_horizontal_overflow_and_theme_persists(page, live_server):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(live_server.url)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=ARTIFACTS / "auth-mobile.png", full_page=True)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.get_by_role("button", name="Alternar tema").click()
    assert page.locator("html").get_attribute("data-theme") == "dark"
    page.reload()
    assert page.locator("html").get_attribute("data-theme") == "dark"


def test_student_manages_subject_task_and_progress(page, live_server):
    console_errors = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text)
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: console_errors.append(str(error)))
    page.goto(live_server.url)
    page.get_by_role("tab", name="Criar conta").click()
    register = page.locator("#register-form")
    register.get_by_label("Nome").fill("Ana Estudante")
    register.get_by_label("E-mail").fill("ana@example.com")
    register.get_by_label("Senha").fill("Senha-Forte-123")
    register.get_by_role("button", name="Cadastrar").click()
    expect(page.get_by_role("heading", name="Olá, Ana")).to_be_visible()
    console_errors.clear()  # Descarta apenas o 401 esperado da consulta de sessão anônima.

    page.get_by_role("link", name="Disciplinas", exact=True).click()
    page.get_by_role("button", name="Nova disciplina").first.click()
    dialog = page.locator("#entity-dialog")
    dialog.get_by_label("Nome da disciplina").fill("Python Aplicado")
    dialog.get_by_label("Carga horária").fill("80")
    dialog.get_by_role("button", name="Salvar").click()
    expect(
        page.locator("#subjects-content").get_by_text("Python Aplicado", exact=True)
    ).to_be_visible()
    page.locator("#toast-region").evaluate("element => element.replaceChildren()")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=ARTIFACTS / "subjects-desktop.png", full_page=True)

    page.get_by_role("link", name="Tarefas", exact=True).click()
    page.get_by_role("button", name="Nova tarefa").first.click()
    dialog.get_by_label("Título").fill("Finalizar exercício")
    dialog.get_by_label("Disciplina").select_option(label="Python Aplicado")
    dialog.get_by_label("Prazo").fill("2026-09-01")
    dialog.get_by_role("button", name="Salvar").click()
    expect(
        page.locator("#tasks-content").get_by_text("Finalizar exercício", exact=True)
    ).to_be_visible()
    page.locator("#toast-region").evaluate("element => element.replaceChildren()")
    page.screenshot(path=ARTIFACTS / "tasks-desktop.png", full_page=True)
    page.get_by_label("Status de Finalizar exercício").select_option("completed")

    page.get_by_role("link", name="Dashboard", exact=True).click()
    expect(page.get_by_text("100%", exact=True).first).to_be_visible()
    expect(page.get_by_role("heading", name="Jornada de aprendizagem")).to_be_visible()
    expect(page.locator("#learning-journey")).to_be_visible()
    journey_stop = page.get_by_role("button", name="Explorar Python Aplicado")
    expect(journey_stop).to_be_visible()
    page.locator("#toast-region").evaluate("element => element.replaceChildren()")
    page.screenshot(path=ARTIFACTS / "dashboard-desktop.png", full_page=True)
    page.set_viewport_size({"width": 1536, "height": 1024})
    journey_stop.click()
    expect(journey_stop).to_have_attribute("aria-expanded", "true")
    expect(journey_stop.locator(".journey-tooltip")).to_be_visible()
    page.wait_for_timeout(250)
    page.screenshot(path=ARTIFACTS / "dashboard-journey-open.png")
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(300)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.screenshot(path=ARTIFACTS / "dashboard-mobile.png", full_page=True)
    assert console_errors == []
