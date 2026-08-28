import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import Settings, get_settings


class EmailService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def build_password_reset_message(
        self, *, to_email: str, reset_url: str
    ) -> EmailMessage:
        message = EmailMessage()
        message["From"] = str(self.settings.smtp_from_email)
        message["To"] = to_email
        message["Subject"] = "Redefina sua senha no EduTrack AI"
        message.set_content(
            "Olá,\n\n"
            "Recebemos uma solicitação para redefinir sua senha no EduTrack AI.\n"
            f"Abra o link abaixo em até {self.settings.password_reset_minutes} minutos:\n\n"
            f"{reset_url}\n\n"
            "Se você não solicitou a alteração, ignore esta mensagem.\n"
        )
        return message

    def send_password_reset(self, *, to_email: str, reset_url: str) -> None:
        message = self.build_password_reset_message(
            to_email=to_email, reset_url=reset_url
        )
        context = ssl.create_default_context()
        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as smtp:
            smtp.starttls(context=context)
            smtp.login(
                str(self.settings.smtp_username), self.settings.smtp_password
            )
            smtp.send_message(message)
