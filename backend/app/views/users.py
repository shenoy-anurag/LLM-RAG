from typing import Any

from fastapi import APIRouter
from fastapi import HTTPException

from app.models.users import UserPublic, UserCreate, UserRegister, UserLogin, UserPublicToken
from app.controllers.users import create_user, get_user_by_email, verify_and_generate_token
from app.core.db import SessionDep


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/signup", response_model=UserPublic)
async def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = create_user(session=session, user_create=user_create)
    return user


@router.post("/login", response_model=UserPublicToken)
async def login_user(session: SessionDep, user_in: UserLogin) -> Any:
    """
    Log in a user.
    """
    user = verify_and_generate_token(
        session=session, email=user_in.email, password=user_in.password)
    print(user)
    return user
