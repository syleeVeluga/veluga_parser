"""
GET  /api/settings/api-keys  — returns { gemini_configured: bool }
POST /api/settings/api-keys  — saves Gemini API key to .env, updates in-process config
"""
import logging

from dotenv import set_key
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import src.backend.config as config
from src.backend.config import BASE_DIR

logger = logging.getLogger(__name__)
router = APIRouter()


class ApiKeyPayload(BaseModel):
    gemini_api_key: str


@router.get("/settings/api-keys")
def get_api_key_status():
    """Returns whether the Gemini API key is configured. Never returns the raw key."""
    return {"gemini_configured": bool(config.GEMINI_API_KEY)}


@router.post("/settings/api-keys")
def save_api_key(payload: ApiKeyPayload):
    """Persist Gemini API key to .env and update in-process config."""
    if not payload.gemini_api_key.strip():
        raise HTTPException(status_code=400, detail="API key cannot be empty")

    env_path = BASE_DIR / ".env"
    try:
        set_key(str(env_path), "GEMINI_API_KEY", payload.gemini_api_key.strip())
    except PermissionError:
        raise HTTPException(
            status_code=500,
            detail=(
                "Cannot write to .env file — permission denied. "
                "Set GEMINI_API_KEY manually in your environment."
            ),
        )
    except Exception as exc:
        logger.exception(f"Failed to write API key to .env: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to persist API key: {exc}")

    # Update in-process config so the current process can use the new key immediately
    config.GEMINI_API_KEY = payload.gemini_api_key.strip()
    logger.info("Gemini API key updated via settings endpoint")
    return {"gemini_configured": True}
