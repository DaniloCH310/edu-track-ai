import json
import re
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
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
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
    register.get_by_label("Senha", exact=True).fill("Senha-Forte-123")
    register.get_by_role("button", name="Cadastrar").click()
    expect(page.get_by_role("heading", name="Olá, Ana")).to_be_visible()
    expect(page.get_by_role("heading", name="Comece em 2 passos")).to_be_visible()
    expect(page.get_by_role("button", name="Criar primeira disciplina")).to_be_visible()

    page.get_by_role("button", name="Sair").click()
    expect(page.get_by_role("heading", name="Bem-vindo de volta")).to_be_visible()
    login = page.locator("#login-form")
    login.get_by_label("E-mail").fill("ana@example.com")
    login.get_by_label("Senha", exact=True).fill("Senha-Forte-123")
    login.get_by_role("button", name="Entrar", exact=True).click()
    expect(page.get_by_role("heading", name="Olá, Ana")).to_be_visible()


def test_password_can_be_revealed_and_hidden_without_losing_its_value(page, live_server):
    password = "Senha-Forte-123"
    page.goto(live_server.url)

    login = page.locator("#login-form")
    login_password = login.locator('input[name="password"]')
    login_password.fill(password)
    login.get_by_role("button", name="Mostrar senha").click()
    expect(login_password).to_have_attribute("type", "text")
    expect(login_password).to_have_value(password)
    login.get_by_role("button", name="Ocultar senha").click()
    expect(login_password).to_have_attribute("type", "password")

    page.get_by_role("tab", name="Criar conta").click()
    register = page.locator("#register-form")
    register_password = register.locator('input[name="password"]')
    register_password.fill(password)
    register.get_by_role("button", name="Mostrar senha").click()
    expect(register_password).to_have_attribute("type", "text")
    expect(register_password).to_have_value(password)

    page.goto(f"{live_server.url}/?reset_token=token-de-teste")
    reset = page.locator("#reset-form")
    reset_password = reset.locator('input[name="new_password"]')
    reset_password.fill(password)
    reset.get_by_role("button", name="Mostrar senha").click()
    expect(reset_password).to_have_attribute("type", "text")
    expect(reset_password).to_have_value(password)


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


def test_classroom_integration_disconnected_and_connected_states(page, live_server):
    connected = False

    def classroom_api(route):
        nonlocal connected
        if route.request.method == "POST":
            connected = True
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "courses_created": 1,
                        "courses_updated": 2,
                        "tasks_created": 3,
                        "tasks_updated": 4,
                        "skipped_without_due_date": 1,
                        "warnings": [],
                    }
                ),
            )
            return
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "available": True,
                    "connected": connected,
                    "last_synced_at": "2026-09-03T12:00:00Z" if connected else None,
                    "last_error_code": None,
                }
            ),
        )

    page.route("**/api/integrations/classroom**", classroom_api)
    page.goto(live_server.url)
    page.get_by_role("tab", name="Criar conta").click()
    register = page.locator("#register-form")
    register.get_by_label("Nome").fill("Ana Estudante")
    register.get_by_label("E-mail").fill("integracoes@example.com")
    register.get_by_label("Senha", exact=True).fill("Senha-Forte-123")
    register.get_by_role("button", name="Cadastrar").click()

    page.get_by_role("link", name="Integrações", exact=True).click()
    classroom = page.locator("#classroom-integration")
    expect(page.get_by_role("heading", name="Integrações")).to_be_visible()
    expect(classroom.get_by_role("heading", name="Google Classroom")).to_be_visible()
    expect(
        classroom.get_by_role("button", name="Conectar Google Classroom")
    ).to_be_visible()

    connected = True
    page.reload()
    sync_button = classroom.get_by_role("button", name="Sincronizar agora")
    expect(sync_button).to_be_visible()
    sync_button.click()
    expect(classroom.get_by_text("Sincronização concluída", exact=True)).to_be_visible()
    expect(classroom.get_by_text("3", exact=True)).to_be_visible()

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    page.set_viewport_size({"width": 1440, "height": 900})
    page.screenshot(path=ARTIFACTS / "integrations-desktop.png", full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(250)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.screenshot(path=ARTIFACTS / "integrations-mobile.png", full_page=True)


def test_student_manages_subject_task_and_progress(page, live_server):
    console_errors = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: console_errors.append(str(error)))
    page.goto(live_server.url)
    page.get_by_role("tab", name="Criar conta").click()
    register = page.locator("#register-form")
    register.get_by_label("Nome").fill("Ana Estudante")
    register.get_by_label("E-mail").fill("ana@example.com")
    register.get_by_label("Senha", exact=True).fill("Senha-Forte-123")
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
        page.get_by_role("button", name="Abrir Python Aplicado")
    ).to_be_visible()
    expect(page.locator("#subjects-overview")).to_be_visible()
    expect(page.locator("#subjects-campus")).to_be_visible()
    subject_building = page.get_by_role("button", name="Abrir Python Aplicado")
    expect(subject_building).to_be_visible()
    subject_building.click()
    subject_detail = page.locator("#subject-detail-panel")
    expect(subject_detail.get_by_role("heading", name="Python Aplicado")).to_be_visible()
    expect(subject_detail.get_by_role("button", name="Editar disciplina")).to_be_visible()
    subject_detail.get_by_role("button", name="Fechar detalhes").click()
    page.get_by_role("button", name="Vista em lista").click()
    expect(page.locator("#subjects-list")).to_be_visible()
    page.get_by_role("button", name="Vista do campus").click()
    page.locator("#toast-region").evaluate("element => element.replaceChildren()")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=ARTIFACTS / "subjects-desktop.png", full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(300)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.screenshot(path=ARTIFACTS / "subjects-mobile.png", full_page=True)
    page.set_viewport_size({"width": 1440, "height": 900})

    page.get_by_role("link", name="Tarefas", exact=True).click()
    page.get_by_role("button", name="Nova tarefa").first.click()
    dialog.get_by_label("Título").fill("Finalizar exercício")
    dialog.get_by_label("Disciplina").select_option(label="Python Aplicado")
    dialog.get_by_label("Prazo").fill("2026-09-01")
    dialog.get_by_role("button", name="Salvar").click()
    tasks_overview = page.locator("#tasks-overview")
    expect(tasks_overview).to_be_visible()
    expect(tasks_overview.get_by_text("1", exact=True).first).to_be_visible()
    task_priority = page.locator("#task-priority")
    expect(task_priority.get_by_role("heading", name="Missão prioritária")).to_be_visible()
    expect(task_priority.get_by_text("Finalizar exercício", exact=True)).to_be_visible()
    mission_board = page.locator("#task-mission-board")
    expect(mission_board).to_be_visible()
    expect(mission_board.locator(".task-mission-card")).to_have_count(1)
    page.get_by_role("button", name="Vista em lista").click()
    expect(page.locator("#tasks-list")).to_be_visible()
    page.get_by_role("button", name="Vista por missões").click()
    expect(mission_board).to_be_visible()
    page.locator("#toast-region").evaluate("element => element.replaceChildren()")
    page.screenshot(path=ARTIFACTS / "tasks-desktop.png", full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(300)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.screenshot(path=ARTIFACTS / "tasks-mobile.png", full_page=True)
    page.set_viewport_size({"width": 1440, "height": 900})

    page.get_by_role("link", name="Dashboard", exact=True).click()
    study_plan = page.locator("#study-plan")
    expect(study_plan.get_by_text("PRÓXIMA MELHOR AÇÃO", exact=True)).to_be_visible()
    expect(study_plan.get_by_text("Finalizar exercício", exact=True)).to_be_visible()
    start_action = study_plan.get_by_role("button", name="Começar agora")
    expect(start_action).to_be_visible()
    start_action.click()
    expect(study_plan.get_by_role("link", name="Continuar tarefa")).to_be_visible()

    page.get_by_role("link", name="Tarefas", exact=True).click()
    task_status = page.locator("#task-mission-board").get_by_label(
        "Status de Finalizar exercício"
    )
    expect(task_status).to_have_value("in_progress")
    task_status.select_option("completed")

    page.get_by_role("link", name="Dashboard", exact=True).click()
    expect(page.get_by_text("100%", exact=True).first).to_be_visible()
    expect(page.get_by_role("heading", name="Campus de aprendizagem")).to_be_visible()
    expect(page.locator("#learning-campus")).to_be_visible()
    campus_building = page.get_by_role("button", name="Explorar Python Aplicado")
    expect(campus_building).to_be_visible()
    expect(campus_building).to_have_class(re.compile(r"\bis-completed\b"))
    milestones = campus_building.locator(".campus-milestones")
    expect(milestones).to_have_attribute("aria-label", "4 de 4 marcos desbloqueados")
    expect(milestones.locator(".is-reached")).to_have_count(4)
    page.locator("#toast-region").evaluate("element => element.replaceChildren()")
    page.screenshot(path=ARTIFACTS / "dashboard-desktop.png", full_page=True)
    page.set_viewport_size({"width": 1440, "height": 1024})
    page.wait_for_timeout(250)
    page.screenshot(path=ARTIFACTS / "dashboard-campus-reference-state.png")
    campus_building.click()
    expect(campus_building).to_have_attribute("aria-expanded", "true")
    expect(campus_building.locator(".campus-tooltip")).to_be_visible()
    page.wait_for_timeout(250)
    page.screenshot(path=ARTIFACTS / "dashboard-campus-open.png")
    campus_building.click()
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(300)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.screenshot(path=ARTIFACTS / "dashboard-mobile.png", full_page=True)
    assert console_errors == []


def test_student_sees_and_updates_task_in_weekly_agenda(page, live_server):
    page.goto(live_server.url)
    page.get_by_role("tab", name="Criar conta").click()
    register = page.locator("#register-form")
    register.get_by_label("Nome").fill("Ana Estudante")
    register.get_by_label("E-mail").fill("ana@example.com")
    register.get_by_label("Senha", exact=True).fill("Senha-Forte-123")
    register.get_by_role("button", name="Cadastrar").click()

    page.get_by_role("link", name="Disciplinas", exact=True).click()
    page.get_by_role("button", name="Nova disciplina").first.click()
    dialog = page.locator("#entity-dialog")
    dialog.get_by_label("Nome da disciplina").fill("Python Aplicado")
    dialog.get_by_label("Carga horária").fill("80")
    dialog.get_by_role("button", name="Salvar").click()

    page.get_by_role("link", name="Tarefas", exact=True).click()
    page.get_by_role("button", name="Nova tarefa").first.click()
    dialog.get_by_label("Título").fill("Finalizar exercício")
    dialog.get_by_label("Disciplina").select_option(label="Python Aplicado")
    dialog.get_by_label("Prazo").fill("2026-09-01")
    dialog.get_by_role("button", name="Salvar").click()

    page.get_by_role("link", name="Agenda", exact=True).click()
    expect(page.get_by_role("heading", name="Agenda semanal")).to_be_visible()
    weekly_route = page.locator("#weekly-route")
    expect(weekly_route).to_be_visible()
    expect(weekly_route.locator(".weekly-route__day")).to_have_count(7)
    expect(weekly_route.locator('[aria-pressed="true"]')).to_have_count(1)
    weekly_summary = page.locator("#weekly-summary")
    expect(
        weekly_summary.get_by_role(
            "heading", name="Você concluiu 0 de 1 tarefa esta semana"
        )
    ).to_be_visible()
    weekly_route.get_by_role("button", name=re.compile(r"1 miss", re.I)).click()
    daily_mission = page.locator("#daily-mission")
    expect(
        daily_mission.get_by_role("heading", name="Missão principal do dia")
    ).to_be_visible()
    expect(daily_mission.get_by_text("Finalizar exercício", exact=True)).to_be_visible()
    expect(
        page.locator("#agenda-subject-progress").get_by_text(
            "Python Aplicado", exact=True
        )
    ).to_be_visible()
    page.locator("#toast-region").evaluate("element => element.replaceChildren()")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    page.set_viewport_size({"width": 1440, "height": 1024})
    page.screenshot(path=ARTIFACTS / "agenda-route-desktop.png", full_page=True)
    daily_mission.get_by_role("button", name="Começar missão").click()
    agenda_status = page.get_by_label("Status de Finalizar exercício na agenda")
    expect(agenda_status).to_have_value("in_progress")
    agenda_status.select_option("completed")
    expect(agenda_status).to_have_value("completed")
    expect(
        weekly_summary.get_by_role(
            "heading", name="Você concluiu 1 de 1 tarefa esta semana"
        )
    ).to_be_visible()
    expect(weekly_summary.get_by_text("Semana concluída!", exact=False)).to_be_visible()

    page.locator("#toast-region").evaluate("element => element.replaceChildren()")
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(300)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.screenshot(path=ARTIFACTS / "agenda-route-mobile.png", full_page=True)
