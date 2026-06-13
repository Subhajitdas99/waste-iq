from pydantic import BaseModel, Field


class CollectorCompleteRequest(BaseModel):
    weight_kg: float = Field(gt=0, le=10000)
