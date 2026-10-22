from app.prompts import CONCRETE_SOCRATIC_PROMPT, MODE_KEYS, PROMPT_MODES


def test_all_three_modes_are_available() -> None:
    assert len(PROMPT_MODES) == 3
    assert set(MODE_KEYS) == {"socratic", "visual", "worked"}


def test_socratic_prompt_keeps_pedagogical_constraints() -> None:
    for phrase in (
        "100% TI\u1ebeNG VI\u1ec6T",
        "ph\u01b0\u01a1ng tr\u00ecnh",
        "hai v\u1ebf",
        "chuy\u1ec3n v\u1ebf",
        "\u0111\u00e1p s\u1ed1 cu\u1ed1i c\u00f9ng",
    ):
        assert phrase in CONCRETE_SOCRATIC_PROMPT
