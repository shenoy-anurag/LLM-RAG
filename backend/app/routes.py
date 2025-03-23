from fastapi import APIRouter

from app.views import users
from app.views import utils
from app.views import chat


api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(chat.router)