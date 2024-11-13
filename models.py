import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID as PyUUID

from sqlalchemy import UUID, Boolean, Column, DateTime, ForeignKeyConstraint, CHAR
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Float, ForeignKey, Integer, LargeBinary, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    uuid = Column(
        CHAR(36),
        primary_key=True,
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    role = Column(String(128), nullable=False, default="user")
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    middle_name = Column(String(128), nullable=True)
    email = Column(String(256), nullable=False)
    phone = Column(String(32), nullable=True)
    password_hash = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    uuid = Column(
        CHAR(36),
        primary_key=True,
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    user_uuid = Column(CHAR(36), ForeignKey("users.uuid"))
    token = Column(String(2048), nullable=False)
    is_active = Column(Boolean, server_default=text("TRUE"), nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    rofl = Column(String(2048), nullable=True)
