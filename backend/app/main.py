import uvicorn
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.routes import api_router
from app.core.config import settings
from app.core.scheduler import lifespan


# function for enabling CORS on web server
def add_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )


app = FastAPI(lifespan=lifespan)


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health-check", status_code=status.HTTP_200_OK)
async def health_check():
    return {"message": "live"}


add_cors(app)

handler = Mangum(app)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
