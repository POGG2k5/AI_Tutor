"""Chay benchmark bon bai Lop 2-5."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.benchmark import ALL_GRADE_TESTS, run_benchmark
from app.config import configure_logging, load_config
from app.model_loader import load_model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "benchmark_results" / "benchmark.md")
    parser.add_argument("--all-grades", action="store_true", help="Chay them bai Lop 1 de co bo Lop 1-5")
    args = parser.parse_args()
    configure_logging()
    config = load_config()
    if args.model:
        config = type(config)(**{**config.__dict__, "model_path": args.model.resolve()})
    model, tokenizer = load_model(config)
    tests = ALL_GRADE_TESTS if args.all_grades else None
    print(run_benchmark(model, tokenizer, config, args.output, tests=tests))


if __name__ == "__main__":
    main()
