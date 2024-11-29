from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import models
from repositories.base import DatabaseRepository


class FarmerRepository(DatabaseRepository[models.Farmer]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.Farmer, session)

    async def find_by_user_uuid(self, user_uuid: UUID) -> Optional[models.Farmer]:
        """Find a farmer by the associated user UUID."""
        async with self.session.begin():
            stmt = select(self.model).where(self.model.user_uuid == str(user_uuid))
            result = await self.session.execute(stmt)
            return result.scalars().first()

    async def create_farmer(
        self,
        user_uuid: UUID,
        government_issued_id: str,
        farm_address: str,
        farm_size: Optional[float] = None,
        additional_info: Optional[str] = None,
    ) -> models.Farmer:
        """Create a new farmer."""
        farmer = models.Farmer(
            user_uuid=str(user_uuid),
            government_issued_id=government_issued_id,
            farm_address=farm_address,
            farm_size=farm_size,
            additional_info=additional_info,
        )
        self.session.add(farmer)
        await self.session.commit()
        return farmer
