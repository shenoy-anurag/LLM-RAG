from pydantic import BaseModel
from fastapi import APIRouter
from fastapi import status
from fastapi.responses import FileResponse


router = APIRouter()


@router.get('/favicon.ico', include_in_schema=False)
async def favicon():
    favicon_path = 'files/favicon.ico'
    return FileResponse(favicon_path)


@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    return {"message": "pong"}
