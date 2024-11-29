from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from dependencies import get_current_user, get_session
from repositories.farmer import FarmerRepository
from schemas.farmer import FarmerCreate, FarmerResponse
from models import User

router = APIRouter(prefix="/farmer", tags=["farmer"])


@router.post(
    "/",
    response_model=FarmerResponse,
    name="Create Farmer Info",
    description="Add farmer-specific information after signup",
)
async def create_farmer_info(
        body: FarmerCreate,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
) -> FarmerResponse:
    repo = FarmerRepository(session)
    existing_farmer = await repo.find_by_user_uuid(user.uuid)
    if existing_farmer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Farmer information already exists for this user.",
        )

    new_farmer = await repo.create_farmer(
        user_uuid=user.uuid,
        government_issued_id=body.government_issued_id,
        farm_address=body.farm_address,
        farm_size=body.farm_size,
        additional_info=body.additional_info,
    )
    return FarmerResponse.model_validate(new_farmer)
