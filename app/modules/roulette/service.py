from __future__ import annotations

import secrets
from threading import Lock


class RouletteSandboxService:
    engine_version = "sandbox-tier-v1"
    required_ad_watches = 5
    default_options = (
        {"id": "common", "label": "Common", "kind": "sandbox_tier", "probability": 0.60, "visualIndex": 0},
        {"id": "uncommon", "label": "Uncommon", "kind": "sandbox_tier", "probability": 0.25, "visualIndex": 1},
        {"id": "rare", "label": "Rare", "kind": "sandbox_tier", "probability": 0.10, "visualIndex": 2},
        {"id": "epic", "label": "Epic", "kind": "sandbox_tier", "probability": 0.04, "visualIndex": 3},
        {"id": "legendary", "label": "Legendary", "kind": "sandbox_tier", "probability": 0.01, "visualIndex": 4},
    )

    def __init__(self) -> None:
        self._lock = Lock()
        self._next_session_id = 1
        self._sessions: dict[int, dict] = {}
        self._test_ad_watches: dict[str, int] = {}

    def _options(self) -> list[dict]:
        return [option.copy() for option in self.default_options]

    def get_progress(self, account_id: str) -> dict:
        with self._lock:
            watched = self._test_ad_watches.get(account_id, 0)
        return {"watched": watched, "required": self.required_ad_watches, "mode": "sandbox"}

    def record_test_ad_watch(self, account_id: str) -> dict:
        with self._lock:
            watched = self._test_ad_watches.get(account_id, 0) + 1
            self._test_ad_watches[account_id] = watched
        return {"watched": watched, "required": self.required_ad_watches, "mode": "sandbox"}

    def create_session(self, account_id: str) -> dict:
        with self._lock:
            session_id = self._next_session_id
            self._next_session_id += 1
            self._sessions[session_id] = {"accountId": account_id, "spun": False}
        return {
            "sessionId": session_id,
            "options": self._options(),
            "engineVersion": self.engine_version,
            "visualSectorCount": len(self.default_options),
            "mode": "sandbox",
        }

    def spin(self, account_id: str, session_id: int, *, random_value: float | None = None) -> dict:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session["accountId"] != account_id:
                raise LookupError("Session not found")
            if session["spun"]:
                raise ValueError("This test session has already been used")

            watched = self._test_ad_watches.get(account_id, 0)
            if watched < self.required_ad_watches:
                raise ValueError(
                    f"Need {self.required_ad_watches} test ad watches to spin (have {watched})"
                )

            draw = secrets.SystemRandom().random() if random_value is None else max(0.0, min(0.999999999, random_value))
            options = self._options()
            cursor = 0.0
            winner = options[-1]
            for option in options:
                cursor += option["probability"]
                if draw < cursor:
                    winner = option
                    break

            session["spun"] = True
            self._test_ad_watches[account_id] = watched - self.required_ad_watches

        return {
            "prize": winner,
            "decision": {
                "engineVersion": self.engine_version,
                "mode": "sandbox",
                "cashValue": False,
                "draw": draw,
            },
        }


roulette_sandbox_service = RouletteSandboxService()
