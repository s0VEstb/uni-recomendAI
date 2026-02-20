from pydantic import BaseModel
from app.db.enums import TagType

class TagOut(BaseModel):
    id: int
    slug: str
    title: str
    type: TagType
    is_active: bool

    model_config = {"from_attributes": True}