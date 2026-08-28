from fastapi.testclient import TestClient

from app.main import create_app


def test_validation_errors_use_the_public_error_envelope():
    """Catches framework-default validation responses leaking into the public contract."""
    application = create_app()

    @application.get("/validation-probe/{value}")
    def validation_probe(value: int):
        return {"value": value}

    with TestClient(application) as client:
        response = client.get("/validation-probe/not-an-integer")

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "validation_error",
            "message": "Revise os campos informados.",
            "fields": {"path.value": "A entrada deve ser um número inteiro válido."},
        }
    }
