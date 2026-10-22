"""Ensure model weights exist locally, downloading them when missing.

Lan chay dau tien tren mot may moi, thu muc ``models/`` chi co ``.gitkeep``.
Module nay se tai LoRA adapter va base model ve ``models/`` theo cau hinh:

- Adapter: ``ADAPTER_REPO`` (repo Hugging Face) hoac Kaggle ``KAGGLE_ADAPTER``.
- Base model: ``BASE_MODEL_REPO`` hoac ``base_model_name_or_path`` trong
  ``adapter_config.json`` (mac dinh ``unsloth/Qwen3-8B-unsloth-bnb-4bit``).

Dat ``AUTO_DOWNLOAD=false`` de tat hoan toan va chi dung model local.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import replace
from pathlib import Path
from typing import Optional

from app.config import PROJECT_ROOT, AppConfig

LOGGER = logging.getLogger(__name__)

MODELS_DIR = PROJECT_ROOT / "models"
DEFAULT_BASE_MODEL_REPO = "unsloth/Qwen3-8B-unsloth-bnb-4bit"
DEFAULT_KAGGLE_ADAPTER = "aegold/math-nckh/transformers/default"
ADAPTER_MARKER = "adapter_config.json"
WEIGHT_SUFFIXES = (".safetensors", ".bin", ".pt")


def _looks_like_hub_id(value: str) -> bool:
    """Return True when the value looks like ``owner/repo`` on the Hub."""
    text = value.strip().rstrip("/")
    if not text or text.startswith((".", "/", "~")):
        return False
    if Path(text).is_absolute() or Path(text).exists():
        return False
    parts = text.split("/")
    return len(parts) == 2 and all(parts)


def _has_weights(path: Path) -> bool:
    if not path.is_dir():
        return False
    return any(p.is_file() and p.suffix in WEIGHT_SUFFIXES for p in path.rglob("*"))


def _snapshot_download(repo_id: str, target: Path) -> Path:
    """Download one Hub repository into ``target`` and return the local path."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise FileNotFoundError(
            "Thieu goi huggingface_hub de tu dong tai model. "
            "Cai bang: pip install -r requirements.txt"
        ) from exc

    token = os.getenv("HF_TOKEN") or None
    target.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Dang tai %s tu Hugging Face vao %s (co the mat vai phut)...", repo_id, target)
    local_path = snapshot_download(repo_id=repo_id, local_dir=str(target), token=token)
    return Path(local_path)


def _find_adapter_dir(root: Path) -> Optional[Path]:
    """Locate the folder that contains ``adapter_config.json`` under ``root``."""
    if (root / ADAPTER_MARKER).is_file():
        return root
    candidates = sorted(root.rglob(ADAPTER_MARKER), key=lambda p: (len(p.parts), str(p)))
    for marker in candidates:
        return marker.parent
    return None


def _adapter_base_repo(adapter_path: Path) -> Optional[str]:
    """Read the Hub id of the base model from ``adapter_config.json``."""
    try:
        data = json.loads((adapter_path / ADAPTER_MARKER).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    base = str(data.get("base_model_name_or_path") or "").strip()
    return base if _looks_like_hub_id(base) else None


def _kaggle_cache_adapter(kaggle_ref: str) -> Optional[Path]:
    """Return an already-downloaded Kaggle model folder, if any.

    ``kagglehub`` doi khi tai xong van nem loi metadata, nen cache local la
    nguon du phong dang tin cay.
    """
    parts = [part for part in kaggle_ref.replace("\\", "/").split("/") if part]
    if len(parts) < 2:
        return None
    cache_root = os.getenv("KAGGLEHUB_CACHE")
    root = Path(cache_root) if cache_root else Path.home() / ".cache" / "kagglehub"
    model_root = root / "models" / parts[0] / parts[1]
    if not model_root.is_dir():
        return None
    return _find_adapter_dir(model_root)


def _download_adapter(target: Path) -> Optional[Path]:
    """Download the LoRA adapter from Hugging Face or Kaggle."""
    repo_id = os.getenv("ADAPTER_REPO", "").strip()
    if repo_id:
        path = _snapshot_download(repo_id, target)
        found = _find_adapter_dir(path)
        if found is None:
            raise FileNotFoundError(
                f"Repo {repo_id} khong chua {ADAPTER_MARKER}. Kiem tra lai ADAPTER_REPO."
            )
        return found

    kaggle_ref = os.getenv("KAGGLE_ADAPTER", DEFAULT_KAGGLE_ADAPTER).strip()
    if not kaggle_ref:
        return None
    cached = _kaggle_cache_adapter(kaggle_ref)
    if cached is not None:
        LOGGER.info("Tim thay adapter Kaggle trong cache: %s", cached)
        return cached
    try:
        import kagglehub
    except ImportError:
        LOGGER.info("kagglehub chua duoc cai; khong the tai adapter tu Kaggle.")
        return None
    try:
        downloaded = Path(kagglehub.model_download(kaggle_ref))
    except Exception as exc:  # noqa: BLE001 - nhieu loi khac nhau tu Kaggle
        LOGGER.warning("Kaggle bao loi khi tai %s: %s", kaggle_ref, exc)
        self_path = _kaggle_cache_adapter(kaggle_ref)
        if self_path is not None:
            LOGGER.info("Dung lai adapter da tai trong cache Kaggle: %s", self_path)
        return self_path
    found = _find_adapter_dir(downloaded)
    if found is None:
        found = _kaggle_cache_adapter(kaggle_ref)
    if found is not None:
        LOGGER.info("Da tai adapter Kaggle vao %s", found)
    return found


def _missing_adapter_message(target: Path) -> str:
    return (
        f"Khong tim thay checkpoint tai {target} va khong tu dong tai duoc.\n"
        "Chon mot trong cac cach sau:\n"
        "  1. Cai kagglehub roi chay lai (model public, khong can dang nhap):\n"
        "     pip install kagglehub\n"
        "     kagglehub.model_download('aegold/math-nckh/transformers/default')\n"
        "  2. Tro den repo Hugging Face: dat ADAPTER_REPO=<user>/<repo> trong .env\n"
        "  3. Chep thu muc checkpoint-30 (co adapter_config.json) vao ./models/\n"
        "Hoac dat AUTO_DOWNLOAD=false neu muon dung model da co san."
    )


def _ensure_adapter(config: AppConfig) -> tuple[Path, bool]:
    """Return (adapter_path, is_adapter), downloading when needed."""
    target = config.model_path.expanduser()
    if target.exists() and (target / ADAPTER_MARKER).is_file():
        return target, True
    if target.exists() and _has_weights(target):
        return target, False
    if not config.auto_download:
        raise FileNotFoundError(_missing_adapter_message(target))

    LOGGER.info("Khong thay model tai %s; bat dau tu dong tai.", target)
    found = _download_adapter(target)
    if found is None:
        raise FileNotFoundError(_missing_adapter_message(target))
    LOGGER.info("Da co adapter tai %s", found)
    return found, True


def _ensure_base_model(config: AppConfig, adapter_path: Path) -> Optional[Path]:
    """Return a local base model path for a LoRA adapter."""
    configured = config.base_model_path.expanduser() if config.base_model_path else None
    if configured is not None and _has_weights(configured):
        return configured

    repo_id = os.getenv("BASE_MODEL_REPO", "").strip() or _adapter_base_repo(adapter_path)
    repo_id = repo_id or DEFAULT_BASE_MODEL_REPO
    target = configured or (MODELS_DIR / repo_id.split("/")[-1])

    if configured is not None and configured.exists() and not _has_weights(configured):
        LOGGER.warning("Thu muc base model %s khong co file trong so; se tai lai.", configured)
    if not config.auto_download:
        raise FileNotFoundError(
            f"Khong tim thay base model tai {target}. Dat BASE_MODEL_PATH den thu muc base model "
            f"hoac bat AUTO_DOWNLOAD de tai {repo_id} tu Hugging Face."
        )

    LOGGER.info("Dang tai base model %s (khoang 5 GB, chi lan dau).", repo_id)
    return _snapshot_download(repo_id, target)


def ensure_models(config: AppConfig) -> AppConfig:
    """Return a config whose model paths exist locally, downloading if allowed."""
    adapter_path, is_adapter = _ensure_adapter(config)
    if not is_adapter:
        return replace(config, model_path=adapter_path)

    base_path = _ensure_base_model(config, adapter_path)
    return replace(config, model_path=adapter_path, base_model_path=base_path)
