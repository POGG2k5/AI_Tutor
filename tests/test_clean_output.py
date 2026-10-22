from app.inference import DEFAULT_SAFE_RESPONSE, clean_model_output


def test_removes_thinking_and_special_tokens() -> None:
    raw = "<think>\u0111o\u1ea1n nh\u1ea9m</think> Th\u1ea7y s\u1ebd g\u1ee3i \u00fd cho em.<|im_end|>"
    assert clean_model_output(raw) == "Th\u1ea7y s\u1ebd g\u1ee3i \u00fd cho em."


def test_removes_english_prefix_before_vietnamese_response() -> None:
    raw = "Okay, let's see. Th\u1ea7y s\u1ebd h\u1ecfi em v\u1ec1 s\u1ed1 18."
    assert clean_model_output(raw) == "Th\u1ea7y s\u1ebd h\u1ecfi em v\u1ec1 s\u1ed1 18."


def test_english_only_response_uses_safe_fallback() -> None:
    assert clean_model_output("The problem is difficult.") == DEFAULT_SAFE_RESPONSE
