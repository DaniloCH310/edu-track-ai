from app.services import email as email_module
from app.services.email import EmailService


def test_password_reset_message_contains_safe_recipient_and_expiring_link():
    """Catches recovery e-mails that omit the user-action link or expiration context."""
    service = EmailService()

    message = service.build_password_reset_message(
        to_email="ana@example.com",
        reset_url="http://127.0.0.1:8000/?reset_token=abc123",
    )

    assert message["To"] == "ana@example.com"
    assert message["From"] == "tests@example.com"
    assert message["Subject"] == "Redefina sua senha no EduTrack AI"
    body = message.get_body(preferencelist=("plain",)).get_content()
    assert "http://127.0.0.1:8000/?reset_token=abc123" in body
    assert "30 minutos" in body
    assert "senha" in body.lower()


def test_password_reset_uses_starttls_login_and_sends_message(monkeypatch):
    calls = []

    class FakeSmtp:
        def __init__(self, host, port):
            calls.append(("connect", host, port))

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def starttls(self, *, context):
            calls.append(("starttls", context is not None))

        def login(self, username, password):
            calls.append(("login", username, password))

        def send_message(self, message):
            calls.append(("send", message["To"]))

    monkeypatch.setattr(email_module.smtplib, "SMTP", FakeSmtp)

    EmailService().send_password_reset(
        to_email="ana@example.com",
        reset_url="http://127.0.0.1:8000/?reset_token=seguro",
    )

    assert calls[0] == ("connect", "smtp.gmail.com", 587)
    assert calls[1] == ("starttls", True)
    assert calls[2] == ("login", "tests@example.com", "not-a-real-password")
    assert calls[3] == ("send", "ana@example.com")
