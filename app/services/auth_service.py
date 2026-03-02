from fastapi import BackgroundTasks

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_reset_token,
    decode_token,
)
from app.db.repositories.user_repo import UserRepo
from app.services.email_service import EmailService


class AuthService:
    def __init__(self, user_repo: UserRepo):
        self.user_repo = user_repo

    async def register(self, email: str, password: str) -> str:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")
        u = await self.user_repo.create(email=email, password_hash=hash_password(password))
        return create_access_token(str(u.id))

    async def login(self, email: str, password: str) -> str:
        u = await self.user_repo.get_by_email(email)
        if not u or not verify_password(password, u.password_hash):
            raise ValueError("Invalid credentials")
        return create_access_token(str(u.id))

    async def request_password_reset(self, email: str, background_tasks: BackgroundTasks, base_url: str) -> None:
        """
        Создание токена сброса и отправка письма.
        """
        user = await self.user_repo.get_by_email(email)
        # чтобы не раскрывать, есть ли пользователь, просто выходим
        if not user:
            return

        token = create_reset_token(str(user.id))
        reset_link = f"{base_url.rstrip('/')}/reset-password?token={token}"

        email_service = EmailService()
        background_tasks.add_task(email_service.send_password_reset, user.email, reset_link)

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Подтверждение сброса пароля по токену.
        """
        payload = decode_token(token)
        if payload.get("scope") != "password_reset":
            raise ValueError("Invalid token scope")

        user_id = int(payload["sub"])
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.password_hash = hash_password(new_password)
        await self.user_repo.update(user)
