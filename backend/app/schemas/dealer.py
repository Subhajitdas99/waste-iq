from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DealerProfileCreate(BaseModel):
    business_name: str = Field(min_length=2, max_length=160)
    owner_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=8, max_length=20)
    address: str = Field(min_length=8, max_length=500)
    city: str = Field(min_length=2, max_length=100)
    pincode: str = Field(min_length=4, max_length=12)
    gst_number: str | None = Field(default=None, max_length=30)
    license_number: str | None = Field(default=None, max_length=50)
    materials_accepted: list[str] = Field(min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class DealerProfileUpdate(BaseModel):
    business_name: str | None = Field(default=None, min_length=2, max_length=160)
    owner_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, min_length=8, max_length=20)
    address: str | None = Field(default=None, min_length=8, max_length=500)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    pincode: str | None = Field(default=None, min_length=4, max_length=12)
    gst_number: str | None = Field(default=None, max_length=30)
    license_number: str | None = Field(default=None, max_length=50)
    materials_accepted: list[str] | None = Field(default=None, min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class DealerProfileRead(BaseModel):
    id: int
    user_id: int
    business_name: str
    owner_name: str
    phone: str
    address: str
    city: str
    pincode: str
    gst_number: str | None
    license_number: str | None
    materials_accepted: list[str]
    verification_status: str
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    profile_completion: int

    model_config = ConfigDict(from_attributes=True)


class AdminDealerSummaryRead(BaseModel):
    user_id: int
    user_name: str
    user_email: str
    account_phone: str
    has_profile: bool
    business_name: str | None
    owner_name: str | None
    city: str | None
    pincode: str | None
    materials_accepted: list[str]
    verification_status: str
    approved_at: datetime | None
    profile_completion: int
    created_at: datetime


class DealerVerificationActionRead(BaseModel):
    user_id: int
    verification_status: str
    approved_at: datetime | None
