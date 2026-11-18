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