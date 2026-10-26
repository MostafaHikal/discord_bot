import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from controllers.InteractionController import InteractionController
from helpers.config import Settings, get_settings
from helpers.signature import is_valid_signature

# The HTTP entry point for Discord: every slash command, button and verification ping arrives here.
# Handles HTTP concerns only (read, authenticate, respond); all decision logic lives in InteractionController.

logger = logging.getLogger("uvicorn.error")

interactions_router = APIRouter(
    prefix="/api/v1",
    tags=["discord"],
)


@interactions_router.post("/interactions")
async def interactions(request: Request, app_settings: Settings = Depends(get_settings)):
    """
    Discord's Interactions Endpoint. Discord expects a response within 3 seconds.
    * Body is read as raw bytes (not a Pydantic model) so the signature is checked before any parsing.
    * Invalid or missing signatures get a 401 and never reach the controller.
    """
    body = await request.body()
    # Missing headers default to "" so they fail verification (401) instead of causing a 500.
    signature = request.headers.get("X-Signature-Ed25519", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")

    if not is_valid_signature(app_settings.DISCORD_PUBLIC_KEY, signature, timestamp, body):
        raise HTTPException(status_code=401, detail="invalid request signature")

    interaction = json.loads(body)
    logger.info("interaction type=%s", interaction.get("type"))

    return InteractionController().handle(interaction)