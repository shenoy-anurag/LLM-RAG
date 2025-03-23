
from sqlmodel import Session, select

from app.core.security import (
    generate_password_hash, verify_password, create_access_token
)
from app.models import User, UserCreate, Token, UserPublicToken


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={
            "password_hash": generate_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def get_user_by_uid(*, session: Session, uid: str) -> User | None:
    statement = select(User).where(User.id == uid)
    session_user = session.exec(statement).first()
    return session_user


def verify_and_generate_token(*, session: Session, email: str, password: str) -> Token | None:
    user = get_user_by_email(session=session, email=email)
    if not user:
        raise ValueError("Incorrect email and password combination!")
    is_authenticated = user.check_password(password=password)
    if not is_authenticated:
        raise ValueError("Incorrect email and password combination!")
    access_token = create_access_token(subject=user.id)
    token = Token(access_token=access_token)
    resp = UserPublicToken(
        email=user.email, first_name=user.first_name, last_name=user.last_name,
        is_superuser=user.is_superuser, id=user.id, token=token
    )
    return resp
