from email.message import EmailMessage
import os
import smtplib
from typing import Optional

from app.core.config import settings


class EmailService:
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        mail_from: Optional[str] = None,
    ):
        # getattr(...) здесь специально: если Settings по какой-то причине
        # создан без этих полей, мы не должны падать 500.
        self.username = (
            username
            or getattr(settings, "MAIL_USERNAME", None)
            or os.getenv("MAIL_USERNAME")
        )
        self.password = (
            password
            or getattr(settings, "APP_PASSWORD", None)
            or os.getenv("APP_PASSWORD")
        )
        self.mail_from = (
            mail_from
            or getattr(settings, "MAIL_FROM", None)
            or os.getenv("MAIL_FROM")
            or self.username
        )

    def _ensure_configured(self) -> None:
        if not self.username or not self.password or not self.mail_from:
            raise RuntimeError("Email settings are not configured")

    def send_password_reset(self, to_email: str, reset_link: str) -> None:
        """
        Отправка письма со ссылкой на сброс пароля через Gmail SMTP.
        """
        self._ensure_configured()

        msg = EmailMessage()
        msg["Subject"] = "Сброс пароля в Uni Recomend"
        msg["From"] = self.mail_from
        msg["To"] = to_email
        msg.set_content(
            f"""Здравствуйте!\n
Вы запросили сброс пароля в сервисе Uni Recomend.\n
Перейдите по ссылке, чтобы установить новый пароль:\n
{reset_link}\n
Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.
"""
        )

        # Gmail SMTP
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)

