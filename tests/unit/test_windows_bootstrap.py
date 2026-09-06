from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def read_project_file(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_windows_cmd_entrypoints_are_portable_and_bypass_process_policy():
    expected_targets = {
        "Instalar EduTrack.cmd": "scripts\\setup-app.ps1",
        "Iniciar EduTrack.cmd": "scripts\\start-app.ps1",
        "Encerrar EduTrack.cmd": "scripts\\stop-postgres.ps1",
    }

    for filename, target in expected_targets.items():
        content = read_project_file(filename)
        assert "%~dp0" in content
        assert "-ExecutionPolicy Bypass" in content
        assert target in content
        assert "C:\\Users\\" not in content


def test_setup_detects_or_installs_a_compatible_python_for_the_current_user():
    setup = read_project_file("scripts/setup-app.ps1")

    assert "3.12" in setup
    assert "winget" in setup
    assert "--scope" in setup and "user" in setup
    assert "-m venv" in setup
    assert 'pip install -e ".[dev]"' in setup


def test_user_instructions_use_portable_cmd_commands():
    instructions = read_project_file("Comando para iniciar servidor.txt")
    readme = read_project_file("README.md")

    assert "Instalar EduTrack.cmd" in instructions
    assert "Iniciar EduTrack.cmd" in instructions
    assert "C:\\Users\\" not in instructions
    assert "py -3 -m venv" not in readme
    assert "Iniciar EduTrack.cmd" in readme


def test_startup_rejects_an_incomplete_copy_or_an_occupied_http_port():
    startup = read_project_file("scripts/start-app.ps1")

    assert "app\\static\\js\\agenda.js" in startup
    assert "app\\static\\css\\campus.css" in startup
    assert "app\\static\\assets\\learning-campus.png" in startup
    assert "Get-NetTCPConnection" in startup
    assert "porta 8000" in startup
