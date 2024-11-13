import logging
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union

from loguru import logger
from sqlalchemy import BinaryExpression, Update, asc, desc, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import RelationshipProperty, selectinload
from sqlalchemy.orm.attributes import InstrumentedAttribute

import models
from domains.base_exception import ServerException

Model = TypeVar("Model", bound=models.Base)


class DatabaseRepository(Generic[Model]):
    """Repository for performing database queries."""

    def __init__(self, model: type[Model], session: AsyncSession) -> None:
        self.model = model
        self.session = session
        self.id_name = inspect(self.model).primary_key[0].name
        self.relationships = self._get_relationships()

    def _get_relationships(self):
        mapper = inspect(self.model)
        relationships = [selectinload(getattr(self.model, relationship.key)) for relationship in mapper.relationships]
        return relationships

    def _extend_query(self, query, expressions):
        if expressions:
            query = query.where(*expressions)
        for relationship in self.relationships:
            query = query.options(relationship)
        return query

    async def create(self, data: dict) -> Model | None:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.commit()

        # Refresh the instance without relationships
        await self.session.refresh(instance)

        id = getattr(instance, self.id_name)

        # Use get_by_id to fetch the instance with relationships
        return await self.get_by_id(id)

    async def batch_create(self, data: List[dict]) -> List[Model]:
        instances = [self.model(**item) for item in data]
        self.session.add_all(instances)
        await self.session.commit()
        for instance in instances:
            await self.session.refresh(instance)
        ids = [getattr(instance, self.id_name) for instance in instances]
        id_column = getattr(self.model, self.id_name)
        query = select(self.model).where(id_column.in_(ids))
        results = await self.session.execute(query)
        return results.unique().scalars().all()

    async def filter(
        self,
        *expressions: BinaryExpression,
        sort_by: Optional[str] = None,
        sort_mode: str = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Model]:
        query = self._extend_query(select(self.model), expressions)

        if sort_by:
            sort_column = getattr(self.model, sort_by)
            query = query.order_by(asc(sort_column) if sort_mode == "asc" else desc(sort_column))

        if offset is not None:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, id: Union[int, str]) -> Model | None:
        query = select(self.model).where(getattr(self.model, self.id_name) == id)
        query = self._extend_query(query, [])
        result = await self.session.execute(query)
        return result.scalars().first()

    async def filterOne(
        self,
        *expressions: BinaryExpression,
    ) -> Model | None:
        x = select(self.model)
        query = self._extend_query(select(self.model), expressions)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def update(self, id: Union[int, str], data: dict) -> Model | None:
        instance = await self.get_by_id(id)
        if not instance:
            return None

        for key, value in data.items():
            attr = getattr(self.model, key, None)
            if isinstance(attr, InstrumentedAttribute) and hasattr(instance, key):
                # Check if it's a relationship and if the value is a dictionary
                if isinstance(attr.property, RelationshipProperty):
                    logger.info("ignoring relationship on updating instance")
                    continue
                setattr(instance, key, value)
            else:
                raise ServerException(f"{self.model.__name__} has no attribute '{key}'")

        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def updateMany(self, expressions: List[BinaryExpression], data: dict) -> List[Model]:
        instances = await self.filter(*expressions)
        logger.info(instances)
        for instance in instances:
            for key, value in data.items():
                setattr(instance, key, value)
        await self.session.commit()
        # Refresh each instance individually
        for instance in instances:
            try:
                logger.info(instance.participant_id, instance.presence_status)
            except:
                pass
            await self.session.refresh(instance)
        return instances

    async def update_batch(self, instances: List[Model]) -> List[Model]:
        # update with just one commit
        await self.session.commit()
        await self.session.refresh(instances)
        return instances

    async def delete(self, id: Union[int, str]) -> None:
        # send delete request to the database directly
        query = self.model.__table__.delete().where(getattr(self.model, self.id_name) == id)
        await self.session.execute(query)
        await self.session.commit()
        return None

    async def deleteMany(self, *expressions: BinaryExpression) -> None:
        query = self.model.__table__.delete().where(*expressions)
        await self.session.execute(query)
        await self.session.commit()
        return None

    # only used for audit
    async def get_second_topmost(
        self,
        field: InstrumentedAttribute,
        *expressions: BinaryExpression,
        order_by: InstrumentedAttribute,
    ) -> Optional[Model]:
        """
        Fetches the latest record based on the specified order_by field and filter expressions.
        """
        query = select(field).where(*expressions).order_by(order_by.desc()).offset(1).limit(1)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_latest_by_condition(
        self,
        field: InstrumentedAttribute,
        *expressions: BinaryExpression,
        order_by: InstrumentedAttribute,
    ) -> Optional[Model]:
        """
        Fetches the latest record based on the specified order_by field and filter expressions.
        """
        query = select(field).where(*expressions).order_by(order_by.desc()).limit(1)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def update_by_condition(
        self,
        model: Model,
        condition: BinaryExpression,
        data: Dict[str, Any],
    ) -> int:
        """
        Update all records in the specified model that match the condition with the values in data.

        :param model: The SQLAlchemy model to update.
        :param condition: The condition to filter the records to be updated.
        :param data: A dictionary of field-value pairs to update.
        :return: The number of rows that were updated.
        """
        stmt: Update = update(model).where(condition).values(**data).execution_options(synchronize_session="fetch")

        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def run_sql(self, sql: str, params={}) -> Any:
        result = await self.session.execute(text(sql), params)
        return result.all()


def get_db_repository(
    model: Type[models.Base],
) -> Callable[[AsyncSession], DatabaseRepository]:
    def func(session: AsyncSession) -> DatabaseRepository:
        return DatabaseRepository(model, session)

    return func
