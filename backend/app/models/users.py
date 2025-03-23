import uuid
from datetime import datetime
from pydantic import EmailStr
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import func

from app.core.security import generate_password_hash, verify_password


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    first_name: str = Field(default=None, max_length=255, nullable=False)
    last_name: str | None = Field(default='', max_length=255, nullable=True)
    is_superuser: bool = False


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    first_name: str = Field(default=None, max_length=255, nullable=False)
    last_name: str | None = Field(default='', max_length=255, nullable=True)


class UserLogin(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)


class User(UserBase, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True, nullable=False
    )
    password_hash: str = Field(max_length=512, nullable=False)
    is_active: bool = True
    created_at: datetime = Field(default_factory=func.now)
    updated_at: datetime = Field(
        default_factory=func.now,
        sa_column_kwargs={"onupdate": func.now()}
    )

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the user's password."""
        return verify_password(password, self.password_hash)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class UserPublicToken(UserBase):
    id: uuid.UUID
    token: Token


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None
