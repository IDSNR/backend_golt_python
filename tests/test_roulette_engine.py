from data_management.roulette_engine import decide_prize, get_default_prizes


def test_default_distribution_has_four_equal_visual_sectors_and_skewed_odds() -> None:
    prizes = get_default_prizes()

    assert len(prizes) == 4
    assert [prize["visualIndex"] for prize in prizes] == [0, 1, 2, 3]
    assert sum(prize["probability"] for prize in prizes) == 1
    assert prizes[0]["probability"] == 0.0001
    assert prizes[1]["probability"] == 0.01
    assert prizes[2]["probability"] == prizes[3]["probability"]


def test_decision_uses_server_distribution_boundaries() -> None:
    prizes = get_default_prizes()

    assert decide_prize(prizes, random_value=0)[0]["id"] == "cash_200"
    assert decide_prize(prizes, random_value=0.0002)[0]["id"] == "cash_2"
    assert decide_prize(prizes, random_value=0.02)[0]["id"] == "custom_hat"
    assert decide_prize(prizes, random_value=0.99)[0]["id"] == "collectable"


def test_decision_records_profile_and_bot_signals_without_changing_placeholder_odds() -> None:
    prizes = get_default_prizes()

    winner, decision = decide_prize(
        prizes,
        profile_metadata={"profile_score": "0.9", "bot_score": "0.1"},
        random_value=0.99,
    )

    assert winner["id"] == "collectable"
    assert decision["engine_version"] == "placeholder-v1"
    assert decision["signals"] == {"profile_score": 0.9, "bot_score": 0.1}
    assert sum(item["probability"] for item in decision["distribution"]) == 1