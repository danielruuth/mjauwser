from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class BreedResponse(BaseModel):
    id: int
    breed_code: str
    name: str
    category_id: Optional[int] = None
    category: Optional[CategoryResponse] = None

    model_config = {"from_attributes": True}


class BreedCreate(BaseModel):
    breed_code: str
    name: str
    category_id: Optional[int] = None


class BreedUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None


class OwnerResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None

    model_config = {"from_attributes": True}


class OwnerCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None


class OwnerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class CatCreate(BaseModel):
    name: str
    breed_ems: str
    gender: str
    show_class: str
    birth_date: Optional[str] = None
    registration_nr: Optional[str] = None
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    status: str = "present"


class CatUpdate(BaseModel):
    name: Optional[str] = None
    breed_ems: Optional[str] = None
    gender: Optional[str] = None
    show_class: Optional[str] = None
    birth_date: Optional[str] = None
    registration_nr: Optional[str] = None
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    status: Optional[str] = None


class CatResponse(BaseModel):
    id: int
    name: str
    breed_ems: str
    breed_name: str = ""
    gender: str
    show_class: str
    birth_date: Optional[str] = None
    registration_nr: Optional[str] = None
    owner: Optional[OwnerResponse] = None
    status: str

    model_config = {"from_attributes": True}


class JudgeCreate(BaseModel):
    name: str
    photo: Optional[str] = None
    bio: Optional[str] = None
    flag: Optional[str] = None
    category_ids: list[int] = []


class JudgeUpdate(BaseModel):
    name: Optional[str] = None
    photo: Optional[str] = None
    bio: Optional[str] = None
    flag: Optional[str] = None
    category_ids: Optional[list[int]] = None


class JudgeResponse(BaseModel):
    id: int
    name: str
    photo: Optional[str] = None
    bio: Optional[str] = None
    flag: Optional[str] = None
    categories: list[CategoryResponse] = []

    model_config = {"from_attributes": True}


class ShowCreate(BaseModel):
    name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "draft"


class ShowUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None


class ShowDayResponse(BaseModel):
    id: int
    show_id: int
    name: str
    sort_order: int

    model_config = {"from_attributes": True}


class ShowDayFullResponse(BaseModel):
    id: int
    show_id: int
    name: str
    sort_order: int
    rings: list["RingResponse"] = []

    model_config = {"from_attributes": True}


class ShowResponse(BaseModel):
    id: int
    name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str
    days: list[ShowDayResponse] = []

    model_config = {"from_attributes": True}


class ShowDetailResponse(BaseModel):
    id: int
    name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str
    days: list[ShowDayFullResponse] = []


class ShowDayCreate(BaseModel):
    name: str
    sort_order: int


class ShowDayUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None


class RingCreate(BaseModel):
    ring_number: int
    judge_id: Optional[int] = None
    category_ids: list[int] = []


class RingUpdate(BaseModel):
    ring_number: Optional[int] = None
    judge_id: Optional[int] = None


class PauseRequest(BaseModel):
    pause_message: Optional[str] = None


class RingResponse(BaseModel):
    id: int
    show_day_id: int
    ring_number: int
    judge: Optional[JudgeResponse] = None
    status: str
    current_catalog_nr: Optional[int] = None
    current_class: Optional[str] = None
    pause_message: Optional[str] = None
    categories: list[CategoryResponse] = []

    model_config = {"from_attributes": True}


class RingQueueCreate(BaseModel):
    cat_id: int
    sequence_order: int


class RingQueueResponse(BaseModel):
    id: int
    ring_id: int
    cat_id: int
    sequence_order: int
    status: str

    model_config = {"from_attributes": True}


class RingQueueItemResponse(BaseModel):
    id: int
    ring_id: int
    cat_id: int
    sequence_order: int
    status: str
    catalog_nr: int | None = None
    cat: CatResponse | None = None


class CatShowDayUpdate(BaseModel):
    catalog_nr: int


class CatShowDayStatusUpdate(BaseModel):
    status: str


class CatShowDayResponse(BaseModel):
    cat_id: int
    show_day_id: int
    catalog_nr: int
    day_name: str = ""
    status: str = "present"

    model_config = {"from_attributes": True}


class CatWithDaysResponse(BaseModel):
    id: int
    name: str
    breed_ems: str
    breed_name: str = ""
    gender: str
    show_class: str
    birth_date: Optional[str] = None
    registration_nr: Optional[str] = None
    owner: Optional[OwnerResponse] = None
    status: str
    days: list[CatShowDayResponse] = []

    model_config = {"from_attributes": True}


class ConnectionResponse(BaseModel):
    id: str
    role: str
    device_type: str | None = None
    device_id: str | None = None
    device_name: str | None = None
    ring_id: int | None = None
    ring_number: int | None = None
    show_id: int | None = None
    day_id: int | None = None
    connected_at: float


class DisplayDeviceResponse(BaseModel):
    id: int
    device_id: str
    name: str
    device_type: str
    show_id: int | None = None
    day_id: int | None = None
    last_connected_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class DisplayDeviceUpdate(BaseModel):
    name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_at: float


class TokenPayload(BaseModel):
    sub: str
    exp: float
    iat: float


class ShowJudgeAdd(BaseModel):
    judge_id: Optional[int] = None
    judge_ids: list[int] = []
    name: Optional[str] = None
    photo: Optional[str] = None
    bio: Optional[str] = None
    flag: Optional[str] = None
    category_ids: list[int] = []


class CatAssignmentProgress(BaseModel):
    total_cats: int
    assigned_cats: int


class StateResponse(BaseModel):
    judges: list[JudgeResponse]
    cats: list[CatResponse]
    shows: list[ShowDetailResponse]
    breeds: list[BreedResponse]
    categories: list[CategoryResponse]


# --- Export / Import ---

class ExportCategory(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


class ExportBreed(BaseModel):
    id: int
    breed_code: str
    name: str
    category_id: Optional[int] = None


class ExportJudge(BaseModel):
    id: int
    name: str
    flag: Optional[str] = None
    category_ids: list[int] = []


class ExportCatDayRef(BaseModel):
    show_day_id: int
    catalog_nr: int


class ExportCat(BaseModel):
    id: int
    name: str
    breed_ems: str
    gender: str
    show_class: str
    birth_date: Optional[str] = None
    registration_nr: Optional[str] = None
    owner: Optional[str] = None
    owner_id: Optional[int] = None
    status: str = "present"
    days: list[ExportCatDayRef] = []


class ExportQueueEntry(BaseModel):
    cat_id: int
    sequence_order: int
    status: str = "pending"


class ExportRing(BaseModel):
    id: int
    ring_number: int
    judge_id: Optional[int] = None
    category_ids: list[int] = []
    queue: list[ExportQueueEntry] = []


class ExportDay(BaseModel):
    id: int
    name: str
    sort_order: int
    rings: list[ExportRing] = []


class ExportShow(BaseModel):
    name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "draft"
    days: list[ExportDay] = []


class ShowExportData(BaseModel):
    version: int = 1
    exported_at: str = ""
    categories: list[ExportCategory]
    breeds: list[ExportBreed]
    judges: list[ExportJudge]
    cats: list[ExportCat]
    show: ExportShow


class ShowImportResponse(BaseModel):
    show_id: int
    categories_found: int = 0
    breeds_found: int = 0
    judges_created: int = 0
    cats_created: int = 0
    queue_entries: int = 0
