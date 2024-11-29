from pydantic import BaseModel
from typing import Optional


class FarmerCreate(BaseModel):
    government_issued_id: str
    farm_address: str
    farm_size: Optional[float] = None
    additional_info: Optional[str] = None


class FarmerResponse(FarmerCreate):
    uuid: str

    class Config:
        from_attributes = True
