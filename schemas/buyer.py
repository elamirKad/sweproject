from pydantic import BaseModel


class BuyerCreate(BaseModel):
    delivery_address: str


class BuyerResponse(BuyerCreate):
    uuid: str

    class Config:
        orm_mode = True
        from_attributes = True
