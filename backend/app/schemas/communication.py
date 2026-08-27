from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ContactSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    pickup_id: int
    status: str
    masked_number: str | None = None
    instructions: str
    expires_at: datetime | None = None
