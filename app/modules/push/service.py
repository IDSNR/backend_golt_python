import re
from typing import Literal

import httpx

from app.core.config import settings


EXPO_PUSH_TOKEN_PATTERN = re.compile(r"^(?:Expo|Exponent)PushToken\[[A-Za-z0-9_-]+\]$")


class PushNotificationService:
    def __init__(self) -> None:
        # Persistence is intentionally left to the database integration owner.
        self.registrations: dict[str, dict[str, dict]] = {}

    def register(self, user_id: str, token: str, platform: Literal["android", "ios"]) -> dict:
        if not EXPO_PUSH_TOKEN_PATTERN.fullmatch(token):
            raise ValueError("Invalid Expo push token")

        registration = {"token": token, "platform": platform}
        self.registrations.setdefault(user_id, {})[token] = registration
        return registration

    def unregister(self, user_id: str, token: str) -> None:
        user_registrations = self.registrations.get(user_id)
        if user_registrations is None:
            return
        user_registrations.pop(token, None)
        if not user_registrations:
            self.registrations.pop(user_id, None)

    def tokens_for_user(self, user_id: str) -> list[str]:
        return list(self.registrations.get(user_id, {}).keys())

    async def send_to_user(
        self,
        user_id: str,
        title: str,
        body: str,
        data: dict[str, object],
    ) -> dict | None:
        tokens = self.tokens_for_user(user_id)
        if not tokens:
            return None

        messages = [
            {"to": token, "sound": "default", "title": title, "body": body, "data": data}
            for token in tokens
        ]
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if settings.expo_push_access_token:
            headers["Authorization"] = f"Bearer {settings.expo_push_access_token}"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(settings.expo_push_url, json=messages, headers=headers)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError):
            # A push outage must not stop an in-app message from being delivered.
            return None
