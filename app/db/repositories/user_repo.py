from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User

class UserRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        res = await self.db.execute(select(User).where(User.email == email))
        return res.scalar_one_or_none()

    async def create(self, email: str, password_hash: str) -> User:
        u = User(email=email, password_hash=password_hash)
        self.db.add(u)
        await self.db.commit()
        await self.db.refresh(u)
        return u

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def update(self, user: User) -> User:
        """
        Обновление пользователя (сохраняет изменения, сделанные с объектом).
        """
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user