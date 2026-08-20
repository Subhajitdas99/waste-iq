from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    role: str
    created_at: datetime
    email_verified: bool
    email_verified_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
