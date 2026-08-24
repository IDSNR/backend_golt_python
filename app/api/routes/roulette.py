from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
import json

from app.api.dependencies import get_current_user
dm_services = None

router = APIRouter(prefix="/roulette", tags=["roulette"])


class RouletteOption(BaseModel):
    id: str
    label: str
    kind: str
    probability: float
    visualIndex: int


class RouletteSessionResponse(BaseModel):
    sessionId: int
    options: List[RouletteOption]
    engineVersion: str
    visualSectorCount: int


class SpinRequest(BaseModel):
    sessionId: int


class SpinResponse(BaseModel):
    prize: dict


@router.get("/session", response_model=RouletteSessionResponse)
def create_session(count: int = 6, current_user: str | None = Depends(get_current_user)) -> dict:
    # normalize account id
    try:
        account_id = int(current_user) if current_user is not None else None
    except Exception:
        account_id = None

    from backend.data_management.roulette_engine import ENGINE_VERSION, get_default_prizes

    opts = get_default_prizes()
    for index, option in enumerate(opts):
        option["visualIndex"] = index

    # lazy import to avoid import-time DB package resolution issues in tests
    global dm_services
    if dm_services is None:
        from backend.data_management import services as _dm
        dm_services = _dm

    session_obj = dm_services.create_roulette_session(created_by_account_id=account_id, options=opts)
    return {"sessionId": session_obj.id, "options": opts, "engineVersion": ENGINE_VERSION, "visualSectorCount": 4}


@router.get("/ads/progress")
def get_ads_progress(current_user: str = Depends(get_current_user)) -> dict:
    try:
        account_id = int(current_user)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid user")

    global dm_services
    if dm_services is None:
        from backend.data_management import services as _dm
        dm_services = _dm

    watched = dm_services.count_ad_watches(account_id=account_id)
    required = 5
    return {"watched": watched, "required": required}


@router.post("/ads/watched")
def post_ad_watched(current_user: str = Depends(get_current_user)) -> dict:
    try:
        account_id = int(current_user)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid user")

    global dm_services
    if dm_services is None:
        from backend.data_management import services as _dm
        dm_services = _dm

    dm_services.record_ad_watch(account_id=account_id)
    watched = dm_services.count_ad_watches(account_id=account_id)
    required = 5
    return {"watched": watched, "required": required}


@router.post("/spin", response_model=SpinResponse)
def spin_roulette(payload: SpinRequest, current_user: str = Depends(get_current_user)) -> dict:
    try:
        account_id = int(current_user)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid user")

    global dm_services
    if dm_services is None:
        from backend.data_management import services as _dm
        dm_services = _dm

    session_obj = dm_services.get_roulette_session(payload.sessionId)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    # Ensure user watched enough ads
    watched = dm_services.count_ad_watches(account_id=account_id)
    required = 5
    if watched < required:
        raise HTTPException(status_code=400, detail=f"Need {required} ad watches to spin (have {watched})")

    options = json.loads(session_obj.options_json or "[]")
    if not options:
        raise HTTPException(status_code=400, detail="No options available")

    metadata_rows = dm_services.retrieve_user_metadata(account_id=account_id)
    metadata = {item.key: item.value for item in metadata_rows}
    from backend.data_management.roulette_engine import decide_prize

    winner, decision = decide_prize(options, profile_metadata=metadata)

    # Record spin and clear ad watches
    spin = dm_services.record_roulette_spin(session_id=session_obj.id, account_id=account_id, prize=winner)
    dm_services.record_roulette_decision(
        spin_id=spin.id,
        account_id=account_id,
        engine_version=decision["engine_version"],
        decision=decision,
    )
    dm_services.clear_ad_watches(account_id=account_id)

    return {"prize": winner, "decision": {"engineVersion": decision["engine_version"]}}
