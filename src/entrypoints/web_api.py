import logging

from fastapi import FastAPI

from api.v1.router import api_router
from api.middleware.auth import populate_user_middleware
from core.config import settings

logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)

app = FastAPI(title=settings.app_name)

app.middleware("http")(populate_user_middleware)

app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
