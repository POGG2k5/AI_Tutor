"""Load a checkpoint with Unsloth or Transformers and PEFT."""

from __future__ import annotations

import json
import logging
from dataclasses import replace
from pathlib import Path
from typing import Any

import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from app.config import AppConfig
from app.model_download import ensure_models

LOGGER = logging.getLogger(__name__)


def _resolve_adapter_base(path: Path, config: AppConfig) -> Path:
    if config.base_model_path is not None:
        base_path = config.base_model_path.expanduser().resolve()
        if not base_path.exists():
            raise FileNotFoundError(
                f"Khong tim thay base model cua LoRA: {base_path}. "
                "Hay dat BASE_MODEL_PATH den thu muc Qwen3-8B local."
            )
        return base_path

    adapter_config_path = path / "adapter_config.json"
    try:
        adapter_config = json.loads(adapter_config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FileNotFoundError(
            f"Khong doc duoc {adapter_config_path}; khong the xac dinh base model LoRA."
        ) from exc

    configured_name = adapter_config.get("base_model_name_or_path")
    if configured_name:
        candidate = Path(configured_name).expanduser()
        if candidate.is_absolute() and candidate.exists():
            return candidate.resolve()
        sibling = path.parent / candidate
        if sibling.exists():
            return sibling.resolve()

    raise FileNotFoundError(
        "Checkpoint la LoRA adapter nhung chua co base model local. "
        "Hay dat BASE_MODEL_PATH den thu muc base model, vi du "
        "models/Qwen3-8B-unsloth-bnb-4bit."
    )


def _resolve_device(device: str) -> str:
    """Select a usable device, preferring CUDA for auto mode."""
    if device.lower() == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device.startswith("cuda") and not torch.cuda.is_available():
        LOGGER.warning("CUDA khong kha dung; chuyen sang CPU.")
        return "cpu"
    return device


def _is_adapter(path: Path) -> bool:
    return (path / "adapter_config.json").is_file()


def _load_with_transformers(path: Path, config: AppConfig, device: str) -> tuple[Any, Any]:
    """Load a full model or LoRA adapter with Transformers/PEFT."""
    adapter = _is_adapter(path)
    base_path = _resolve_adapter_base(path, config) if adapter else path
    tokenizer = AutoTokenizer.from_pretrained(str(path), trust_remote_code=True)
    kwargs: dict[str, Any] = {"trust_remote_code": True}
    if device == "cuda":
        model_config = AutoConfig.from_pretrained(str(base_path), trust_remote_code=True)
        kwargs["device_map"] = {"": 0}
        kwargs["torch_dtype"] = torch.float16
        if config.load_in_4bit:
            try:
                import bitsandbytes
                kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                    llm_int8_enable_fp32_cpu_offload=True,
                )
                kwargs["max_memory"] = {0: "5.5GiB"}
                if isinstance(model_config.quantization_config, dict):
                    model_config.quantization_config["llm_int8_enable_fp32_cpu_offload"] = True
                else:
                    model_config.quantization_config.llm_int8_enable_fp32_cpu_offload = True
                kwargs["config"] = model_config
            except ImportError:
                LOGGER.warning("bitsandbytes chua duoc cai; nap model CUDA khong quantize 4-bit.")
    else:
        kwargs["torch_dtype"] = torch.float32
    if adapter:
        from peft import PeftModel
        base_model = AutoModelForCausalLM.from_pretrained(str(base_path), **kwargs)
        model = PeftModel.from_pretrained(base_model, str(path), is_trainable=False)
    else:
        model = AutoModelForCausalLM.from_pretrained(str(path), **kwargs)
        if device == "cpu":
            model.to(device)
    model.eval()
    return model, tokenizer


def load_model(config: AppConfig) -> tuple[Any, Any]:
    """Try Unsloth first, then fall back to Transformers and PEFT."""
    config = ensure_models(config)
    path = config.model_path.expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(
            f"Khong tim thay checkpoint: {path}. Hay chep checkpoint-30 vao thu muc models/."
        )
    device = _resolve_device(config.device)
    if config.load_in_4bit and device == "cpu":
        LOGGER.warning("load_in_4bit chi bat tren CUDA; model se duoc nap dang thuong tren CPU.")
    try:
        from unsloth import FastLanguageModel
        LOGGER.info("Dang nap model bang Unsloth tu %s", path)
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=str(path),
            max_seq_length=config.max_seq_len,
            load_in_4bit=config.load_in_4bit and device == "cuda",
        )
        model.eval()
        return model, tokenizer
    except ImportError:
        LOGGER.info("Unsloth chua duoc cai; dung Transformers + PEFT.")
    except Exception:
        LOGGER.exception("Unsloth khong nap duoc model; thu fallback Transformers + PEFT.")
    try:
        return _load_with_transformers(path, config, device)
    except Exception:
        if device != "cuda":
            raise
        LOGGER.exception("Khong the nap 4-bit voi CPU offload; thu lai bang CPU.")
        cpu_config = replace(config, device="cpu")
        return _load_with_transformers(path, cpu_config, "cpu")
