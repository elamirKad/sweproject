from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from database import get_session
from dependencies import get_current_user
from models import User
from repositories.buyer import BuyerRepository
from schemas.buyer import BuyerResponse, BuyerCreate

router = APIRouter(prefix="/buyer", tags=["buyer"])


@router.post(
    "/",
    response_model=BuyerResponse,
    name="Create Buyer Info",
    description="Add buyer-specific information after signup",
)
async def create_buyer_info(
        body: BuyerCreate,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
) -> BuyerResponse:
    repo = BuyerRepository(session)
    existing_buyer = await repo.find_by_user_uuid(user.uuid)
    if existing_buyer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Buyer information already exists for this user.",
        )

    new_buyer = await repo.create_buyer(user_uuid=user.uuid, delivery_address=body.delivery_address)
    return BuyerResponse.model_validate(new_buyer)
