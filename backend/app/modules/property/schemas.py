from pydantic import BaseModel
from typing import Optional, Any

class CreatePropertyRequest(BaseModel):
    property_name: str
    address: str
    property_type: str = "SELF_BUILT"

class CreateRoomRequest(BaseModel):
    property_id: str
    room_number: str
    room_type: str = "RENTAL"
    room_name: Optional[str] = None
    layout: Optional[dict[str, Any]] = None

from typing import Optional

class CreateMeterRequest(BaseModel):
    meter_type: str # ELECTRIC, COLD_WATER, HOT_WATER
    meter_number: str
    initial_reading: float = 0.0

class BatchCreateFloor(BaseModel):
    floor_number: int
    room_count: int
    room_type: str # RENTAL, SHOP, SELF_USE
    has_hot_water: bool = True
    has_cold_water: bool = True
    has_electric: bool = True

class BatchCreatePropertyRequest(BaseModel):
    property_name: str
    address: str
    floors: list[BatchCreateFloor]

from datetime import date

class SignTenancyRequest(BaseModel):
    tenant_name: str
    tenant_phone: str
    monthly_rent: float
    deposit_amount: float
    start_date: str  # YYYY-MM-DD
    end_date: str

class RecordPaymentRequest(BaseModel):
    amount: float
    payer_name: str
    channel: str = "WECHAT"

class WriteOffRequest(BaseModel):
    bill_id: str
    amount: float