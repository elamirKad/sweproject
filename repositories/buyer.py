from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import models
from repositories.base import DatabaseRepository


class BuyerRepository(DatabaseRepository[models.Buyer]):
    def __init__(self, session: AsyncSession):
        super().__init__(models.Buyer, session)

    async def find_by_user_uuid(self, user_uuid: UUID) -> Optional[models.Buyer]:
        """Find a buyer by the associated user UUID."""
        async with self.session.begin():
            stmt = select(self.model).where(self.model.user_uuid == str(user_uuid))
            result = await self.session.execute(stmt)
            return result.scalars().first()

    async def create_buyer(
        self,
        user_uuid: UUID,
        delivery_address: str,
    ) -> models.Buyer:
        """Create a new buyer."""
        buyer = models.Buyer(
            user_uuid=str(user_uuid),
            delivery_address=delivery_address,
        )
        self.session.add(buyer)
        await self.session.commit()
        return buyer
