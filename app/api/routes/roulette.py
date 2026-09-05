import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.modules.roulette.service import roulette_sandbox_service


router = APIRouter(prefix="/roulette", tags=["roulette"])


class RouletteOption(BaseModel):
    id: str
    label: str
    kind: str
    probability: float
    visualIndex: int


class RouletteSessionResponse(BaseModel):
    sessionId: int
    options: list[RouletteOption]
    engineVersion: str
    visualSectorCount: int
    mode: str


class SpinRequest(BaseModel):
    sessionId: int


class SpinResponse(BaseModel):
    prize: dict
    decision: dict


def roulette_status() -> dict:
    requested = os.getenv("ROULETTE_SANDBOX_ENABLED", "false").lower() == "true"
    production = os.getenv("APP_ENV", "development").lower() in {"production", "prod"}
    enabled = requested and not production
    if production:
        reason = "The Spin Lab cannot run in production until legal, licence, age, location, and store approvals are complete."
    elif not requested:
        reason = "The Spin Lab is disabled. Set ROULETTE_SANDBOX_ENABLED=true in a development environment to test it."
    else:
        reason = "Development sandbox only. Results have no cash or real-world value."
    return {
        "enabled": enabled,
        "mode": "sandbox" if enabled else "disabled",
        "cashValue": False,
        "requiredTestAdWatches": roulette_sandbox_service.required_ad_watches,
        "reason": reason,
    }


def require_roulette_sandbox() -> None:
    availability = roulette_status()
    if not availability["enabled"]:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=availability["reason"])


@router.get("/status")
def get_roulette_status() -> dict:
    return roulette_status()


@router.get("/session", response_model=RouletteSessionResponse)
def create_session(current_user: str = Depends(get_current_user)) -> dict:
    require_roulette_sandbox()
    return roulette_sandbox_service.create_session(current_user)


@router.get("/ads/progress")
def get_ads_progress(current_user: str = Depends(get_current_user)) -> dict:
    require_roulette_sandbox()
    return roulette_sandbox_service.get_progress(current_user)


@router.post("/ads/watched")
def post_ad_watched(current_user: str = Depends(get_current_user)) -> dict:
    require_roulette_sandbox()
    return roulette_sandbox_service.record_test_ad_watch(current_user)


@router.post("/spin", response_model=SpinResponse)
def spin_roulette(payload: SpinRequest, current_user: str = Depends(get_current_user)) -> dict:
    require_roulette_sandbox()
    try:
        return roulette_sandbox_service.spin(current_user, payload.sessionId)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
