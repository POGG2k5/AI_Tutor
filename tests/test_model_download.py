import json
from pathlib import Path

import pytest

from app.config import AppConfig
from app.model_download import (
    ADAPTER_MARKER,
    _find_adapter_dir,
    _looks_like_hub_id,
    ensure_models,
)


def _make_adapter(root: Path) -> Path:
    path = root / "checkpoint-30"
    path.mkdir(parents=True)
    (path / ADAPTER_MARKER).write_text(
        json.dumps({"base_model_name_or_path": "unsloth/Qwen3-8B-unsloth-bnb-4bit"}),
        encoding="utf-8",
    )
    return path


def _make_base(root: Path) -> Path:
    path = root / "base"
    path.mkdir(parents=True)
    (path / "model.safetensors").write_bytes(b"0")
    return path


def test_hub_id_detection() -> None:
    assert _looks_like_hub_id("unsloth/Qwen3-8B-unsloth-bnb-4bit")
    assert not _looks_like_hub_id("./models/checkpoint-30")
    assert not _looks_like_hub_id("models")
    assert not _looks_like_hub_id("a/b/c")
    assert not _looks_like_hub_id("")


def test_find_adapter_dir_handles_nested_output(tmp_path: Path) -> None:
    nested = tmp_path / "output" / "checkpoint"
    nested.mkdir(parents=True)
    (nested / ADAPTER_MARKER).write_text("{}", encoding="utf-8")
    assert _find_adapter_dir(tmp_path) == nested


def test_local_models_are_used_without_download(tmp_path: Path) -> None:
    adapter = _make_adapter(tmp_path)
    base = _make_base(tmp_path)
    resolved = ensure_models(
        AppConfig(model_path=adapter, base_model_path=base, auto_download=True)
    )
    assert resolved.model_path == adapter
    assert resolved.base_model_path == base


def test_full_model_directory_needs_no_base_model(tmp_path: Path) -> None:
    model = tmp_path / "full-model"
    model.mkdir()
    (model / "config.json").write_text("{}", encoding="utf-8")
    (model / "model.safetensors").write_bytes(b"0")
    resolved = ensure_models(AppConfig(model_path=model, auto_download=False))
    assert resolved.model_path == model
    assert resolved.base_model_path is None


def test_missing_model_raises_when_download_disabled(tmp_path: Path) -> None:
    config = AppConfig(model_path=tmp_path / "missing", auto_download=False)
    with pytest.raises(FileNotFoundError):
        ensure_models(config)
