"""Load YAML configuration and environment overrides."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(_: Path) -> None:
        """No-op when optional dotenv support is unavailable."""
        return None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
load_dotenv(PROJECT_ROOT / ".env")


def _as_bool(value: Any) -> bool:
    """Convert a configuration value to bool."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AppConfig:
    """Application configuration and checkpoint location."""

    model_path: Path
    base_model_path: Optional[Path] = None
    max_seq_len: int = 4096
    load_in_4bit: bool = True
    device: str = "auto"
    temperature: float = 0.25
    top_p: float = 0.85
    repetition_penalty: float = 1.15
    log_level: str = "INFO"
    auto_download: bool = True


def load_config(config_path: Path | str = CONFIG_PATH) -> AppConfig:
    """Load YAML and apply supported environment variable overrides."""
    path = Path(config_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    data = data or {}
    model = data.get("model", {})
    generation = data.get("generation", {})
    logging_config = data.get("logging", {})
    model_path = Path(os.getenv("MODEL_PATH", model.get("path", "./models/checkpoint-30")))
    if not model_path.is_absolute():
        model_path = PROJECT_ROOT / model_path
    base_model_value = os.getenv('BASE_MODEL_PATH', model.get('base_path'))
    base_model_path = None
    if base_model_value:
        base_model_path = Path(base_model_value)
        if not base_model_path.is_absolute():
            base_model_path = PROJECT_ROOT / base_model_path
    return AppConfig(
        model_path=model_path,
        base_model_path=base_model_path,
        max_seq_len=int(os.getenv("MAX_SEQ_LEN", model.get("max_seq_len", 4096))),
        load_in_4bit=_as_bool(os.getenv("LOAD_IN_4BIT", model.get("load_in_4bit", True))),
        device=os.getenv("DEVICE", model.get("device", "auto")),
        temperature=float(generation.get("temperature", 0.25)),
        top_p=float(generation.get("top_p", 0.85)),
        repetition_penalty=float(generation.get("repetition_penalty", 1.15)),
        log_level=os.getenv("LOG_LEVEL", logging_config.get("level", "INFO")).upper(),
        auto_download=_as_bool(os.getenv("AUTO_DOWNLOAD", model.get("auto_download", True))),
    )


def configure_logging(level: str | None = None) -> None:
    """Configure logging for command-line entry points."""
    selected = level or load_config().log_level
    logging.basicConfig(
        level=getattr(logging, selected.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
