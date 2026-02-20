from pydantic import BaseModel, EmailStr
from app.db.enums import UserRole

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}