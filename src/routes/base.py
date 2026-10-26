from fastapi import APIRouter, Depends
from helpers.config import Settings, get_settings

# Health/welcome endpoint: a quick way to confirm the server is up and the environment loaded correctly.

base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)

@base_router.get("/")
async def welcome(app_settings: Settings = Depends(get_settings)):
    # Public and touches no database or external service; exposes only the non-sensitive name and version.
    return {
        "app_name": app_settings.APP_NAME,
        "app_version": app_settings.APP_VERSION,
    }