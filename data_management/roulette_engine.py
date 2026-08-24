from __future__ import annotations

import random
from typing import Any, Optional


ENGINE_VERSION = "placeholder-v1"

# The wheel is always visually divided into four equal sectors. These are
# outcome probabilities, intentionally kept separate from visual geometry.
DEFAULT_PRIZES = [
    {"id": "cash_200", "label": "€200", "kind": "cash", "probability": 0.0001, "visualIndex": 0},
    {"id": "cash_2", "label": "€2", "kind": "cash", "probability": 0.01, "visualIndex": 1},
    {"id": "custom_hat", "label": "Customizable hat", "kind": "hat", "probability": 0.49495, "visualIndex": 2},
    {"id": "collectable", "label": "Collectable", "kind": "collectable", "probability": 0.49495, "visualIndex": 3},
]


def get_default_prizes() -> list[dict[str, Any]]:
    return [prize.copy() for prize in DEFAULT_PRIZES]


def _profile_signals(profile_metadata: Optional[dict[str, Any]]) -> dict[str, float]:
    metadata = profile_metadata or {}
    try:
        bot_score = max(0.0, min(1.0, float(metadata.get("bot_score", 0.5))))
    except (TypeError, ValueError):
        bot_score = 0.5
    try:
        profile_score = max(0.0, min(1.0, float(metadata.get("profile_score", 0.5))))
    except (TypeError, ValueError):
        profile_score = 0.5
    return {"bot_score": bot_score, "profile_score": profile_score}


def decide_prize(
    options: list[dict[str, Any]],
    *,
    profile_metadata: Optional[dict[str, Any]] = None,
    random_value: Optional[float] = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    signals = _profile_signals(profile_metadata)
    # Placeholder policy: keep the launch distribution unchanged while making
    # the signal inputs explicit for a future calibrated policy.
    probabilities = [float(option.get("probability", 0.0)) for option in options]
    total = sum(probabilities)
    if not options or total <= 0:
        raise ValueError("Roulette options must contain positive probability")

    draw = random.random() if random_value is None else max(0.0, min(0.999999999, random_value))
    cursor = 0.0
    winner = options[-1]
    for option, probability in zip(options, probabilities):
        cursor += probability / total
        if draw < cursor:
            winner = option
            break

    decision = {
        "engine_version": ENGINE_VERSION,
        "draw": draw,
        "signals": signals,
        "distribution": [
            {"id": option.get("id"), "probability": probability / total}
            for option, probability in zip(options, probabilities)
        ],
    }
    return winner, decision