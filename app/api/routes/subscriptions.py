from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.services import notification_service, subscription_service

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


class SubscriptionCreateRequest(BaseModel):
    creatorId: str


class PlanUpdateRequest(BaseModel):
    priceCents: int
    enabled: bool = True


@router.post("", status_code=status.HTTP_201_CREATED)
def create_subscription(payload: SubscriptionCreateRequest, current_user: str = Depends(get_current_user)) -> dict:
    subscriber_profile_id = current_user
    try:
        subscription = subscription_service.subscribe(subscriber_profile_id, payload.creatorId)
    except ValueError as exc:
        error_message = str(exc)
        if error_message == 'Subscriptions are not enabled for this creator':
            raise HTTPException(status_code=404, detail=error_message) from exc
        if error_message == 'Already subscribed':
            raise HTTPException(status_code=409, detail=error_message) from exc
        raise HTTPException(status_code=402, detail=error_message) from exc

    notification_service.send_notification(
        payload.creatorId,
        'new_subscriber',
        {
            'subscriberId': subscriber_profile_id,
            'creatorId': payload.creatorId,
            'subscriptionId': subscription['id'],
            'priceCents': subscription_service.get_plan(payload.creatorId)['price_cents'],
        },
    )

    return {"subscription": subscription}


@router.post("/{creator_profile_id}/cancel")
def cancel_subscription(creator_profile_id: str, current_user: str = Depends(get_current_user)) -> dict:
    try:
        subscription = subscription_service.cancel_subscription(current_user, creator_profile_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"subscription": subscription}


@router.get("/mine/{creator_profile_id}")
def get_my_subscription(creator_profile_id: str, current_user: str = Depends(get_current_user)) -> dict:
    subscription = subscription_service.get_subscription(current_user, creator_profile_id)
    return {"subscription": subscription}


@router.get("/plan/{creator_profile_id}")
def get_subscription_plan(creator_profile_id: str) -> dict:
    plan = subscription_service.get_plan(creator_profile_id)
    return {"plan": plan}


@router.put("/plan")
def update_subscription_plan(payload: PlanUpdateRequest, current_user: str = Depends(get_current_user)) -> dict:
    try:
        plan = subscription_service.set_subscription_price(current_user, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"plan": plan}
