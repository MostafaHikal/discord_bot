import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from controllers.InteractionController import InteractionController
from helpers.config import Settings, get_settings
from helpers.signature import is_valid_signature

logger = logging.getLogger("uvicorn.error")

interactions_router = APIRouter(
    prefix="/api/v1",
    tags=["discord"],
)


@interactions_router.post("/interactions")
async def interactions(request: Request, app_settings: Settings = Depends(get_settings)):
    body = await request.body()
    signature = request.headers.get("X-Signature-Ed25519", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")

    if not is_valid_signature(app_settings.DISCORD_PUBLIC_KEY, signature, timestamp, body):
        raise HTTPException(status_code=401, detail="invalid request signature")

    interaction = json.loads(body)
    logger.info("interaction type=%s", interaction.get("type"))

    return InteractionController().handle(interaction)