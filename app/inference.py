"""Sinh phan hoi su pham va quan ly ngu canh hoi thoai nhieu luot."""

from __future__ import annotations

import logging
import re
from typing import Any

from app.config import AppConfig, load_config

LOGGER = logging.getLogger(__name__)
ENGLISH_THOUGHT_STARTERS = (
    "okay, let's see", "first, let's", "the student is", "the problem is",
    "let me see", "we need to solve", "hmm, how do i", "starting with",
)
DEFAULT_SAFE_RESPONSE = (
    "Ch\u00e0o em! Trong b\u00e0i to\u00e1n n\u00e0y, em h\u00e3y ch\u00fa \u00fd \u0111\u1ebfn ph\u00e9p t\u00ednh c\u00f3 ch\u1ee9a x tr\u01b0\u1edbc nh\u00e9. "
    "Em h\u00e3y cho th\u1ea7y bi\u1ebft ph\u00e9p t\u00ednh n\u00e0y g\u1ed3m nh\u1eefng th\u00e0nh ph\u1ea7n n\u00e0o?"
)


def clean_model_output(raw_text: str) -> str:
    """Loc the suy nghi, token dieu khien va doan nham tieng Anh dau ra."""
    cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL)
    cleaned = re.sub(r"^.*?</think>", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.replace("<|im_end|>", "").replace("<think>", "").replace("</think>", "").strip()
    if cleaned.lower().startswith(ENGLISH_THOUGHT_STARTERS):
        vietnamese_match = re.search(
            r"(Ch\u00e0o em|Th\u1ea7y|C\u00f4|Trong ph\u00e9p|\u0110\u1ec3 t\u00ecm|B\u00e0i to\u00e1n|Tr\u01b0\u1edbc ti\u00ean)",
            cleaned,
            re.IGNORECASE,
        )
        cleaned = cleaned[vietnamese_match.start():].strip() if vietnamese_match else DEFAULT_SAFE_RESPONSE
    return cleaned.strip()


class PedagogicalInference:
    """Bao model va tokenizer de thuc hien suy luan."""

    def __init__(self, model: Any, tokenizer: Any, config: AppConfig | None = None) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.config = config or load_config()

    def generate(
        self,
        messages: list[dict[str, str]],
        *,
        enable_thinking: bool = False,
        max_new_tokens: int = 400,
        temp: float = 0.25,
    ) -> str:
        """Sinh cau tra loi voi tham so lay tu notebook."""
        chat_prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=enable_thinking
        )
        inputs = self.tokenizer(chat_prompt, return_tensors="pt")
        input_device = getattr(self.model, "device", None)
        if input_device is not None:
            inputs = inputs.to(input_device)
        output_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temp,
            top_p=self.config.top_p,
            repetition_penalty=self.config.repetition_penalty,
            do_sample=True,
        )
        generated_tokens = output_ids[0][inputs.input_ids.shape[1]:]
        raw_response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        return clean_model_output(raw_response)


def run_pedagogical_inference(
    user_text: str,
    system_prompt: str,
    model: Any,
    tokenizer: Any,
    enable_thinking: bool = False,
    max_new_tokens: int = 400,
    temp: float = 0.25,
    config: AppConfig | None = None,
) -> str:
    """Sinh mot phan hoi doc lap cho de bai."""
    engine = PedagogicalInference(model, tokenizer, config)
    return engine.generate(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_text}],
        enable_thinking=enable_thinking, max_new_tokens=max_new_tokens, temp=temp,
    )


class MultiTurnMathSession:
    """Giu lich su system/user/assistant de chat noi tiep."""

    def __init__(
        self, model: Any, tokenizer: Any, system_prompt: str, config: AppConfig | None = None
    ) -> None:
        self.engine = PedagogicalInference(model, tokenizer, config)
        self.system_prompt = system_prompt
        self.history: list[dict[str, str]] = []
        self.reset()

    def reset(self, system_prompt: str | None = None) -> None:
        """Bat dau hoi thoai moi, tuy chon doi che do su pham."""
        if system_prompt is not None:
            self.system_prompt = system_prompt
        self.history = [{"role": "system", "content": self.system_prompt}]

    def send_message(self, user_text: str) -> str:
        """Gui tin nhan va them ca hai luot vao lich su."""
        text = user_text.strip()
        if not text:
            raise ValueError("Tin nhan khong duoc de trong.")
        self.history.append({"role": "user", "content": text})
        try:
            response = self.engine.generate(
                self.history, enable_thinking=False, max_new_tokens=300, temp=0.25
            )
        except Exception:
            self.history.pop()
            LOGGER.exception("Sinh phan hoi hoi thoai that bai.")
            raise
        self.history.append({"role": "assistant", "content": response})
        return response
