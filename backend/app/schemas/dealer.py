from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.dealer_profile import DealerApprovalStatus

PHONE_PATTERN = r"^\+?[0-9]{10,15}$"


class DealerProfileBase(BaseModel):
    business_name: str = Field(min_length=2, max_length=160)
    owner_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=8, max_length=20, pattern=PHONE_PATTERN)
    email: EmailStr | None = None
    address: str = Field(min_length=8, max_length=500)
    city: str = Field(min_length=2, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str = Field(min_length=4, max_length=12)
    gst_number: str | None = Field(default=None, max_length=30)
    license_number: str | None = Field(default=None, max_length=50)
    business_type: str | None = Field(default=None, max_length=50)
    profile_image: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    materials_accepted: list[str] = Field(min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class DealerProfileCreate(DealerProfileBase):
    pass


class DealerProfileUpdate(BaseModel):
    business_name: str | None = Field(default=None, min_length=2, max_length=160)
    owner_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, min_length=8, max_length=20, pattern=PHONE_PATTERN)
    email: EmailStr | None = None
    address: str | None = Field(default=None, min_length=8, max_length=500)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, min_length=4, max_length=12)
    gst_number: str | None = Field(default=None, max_length=30)
    license_number: str | None = Field(default=None, max_length=50)
    business_type: str | None = Field(default=None, max_length=50)
    profile_image: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    materials_accepted: list[str] | None = Field(default=None, min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class DealerProfileRead(BaseModel):
    id: int
    user_id: int
    business_name: str
    owner_name: str
    phone: str
    email: str | None
    address: str
    city: str
    state: str | None
    postal_code: str
    gst_number: str | None
    license_number: str | None
    business_type: str | None
    profile_image: str | None
    description: str | None
    materials_accepted: list[str]
    approval_status: DealerApprovalStatus
    rejection_reason: str | None
    is_verified: bool
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    profile_completion: int

    model_config = ConfigDict(from_attributes=True)


class DealerApprovalEventRead(BaseModel):
    id: int
    status: DealerApprovalStatus
    note: str | None
    actor_name: str | None
    actor_role: str | None
    created_at: datetime

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
    postal_code: str | None
    materials_accepted: list[str]
    approval_status: DealerApprovalStatus
    rejected_reason: str | None
    approved_at: datetime | None
    profile_completion: int
    created_at: datetime


class AdminDealerListPageRead(BaseModel):
    items: list[AdminDealerSummaryRead]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class AdminDealerDetailRead(BaseModel):
    user_id: int
    user_name: str
    user_email: str
    account_phone: str
    profile: DealerProfileRead
    timeline: list[DealerApprovalEventRead]


class DealerApprovalActionRead(BaseModel):
    profile_id: int
    user_id: int
    approval_status: DealerApprovalStatus
    rejection_reason: str | None
    is_verified: bool
    approved_at: datetime | None
    updated_at: datetime


class DealerRejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
