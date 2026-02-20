from app.core.security import hash_password, verify_password, create_access_token
from app.db.repositories.user_repo import UserRepo

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