"""Chay bon bai benchmark tieu hoc tu notebook va xuat Markdown."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import AppConfig
from app.inference import run_pedagogical_inference
from app.prompts import CONCRETE_SOCRATIC_PROMPT

ELEMENTARY_TESTS = [
    {"grade": "L\u1edbp 2", "topic": "T\u00ecm th\u00e0nh ph\u1ea7n ch\u01b0a bi\u1ebft", "prompt": "T\u00ecm x, bi\u1ebft: x + 18 = 45"},
    {"grade": "L\u1edbp 3", "topic": "T\u00ecm th\u1eeba s\u1ed1 ch\u01b0a bi\u1ebft", "prompt": "T\u00ecm x, bi\u1ebft: x * 4 = 36"},
    {"grade": "L\u1edbp 4", "topic": "To\u00e1n T\u1ed5ng - Hi\u1ec7u", "prompt": "Hai b\u1ea1n An v\u00e0 B\u00ecnh c\u00f3 t\u1ed5ng c\u1ed9ng 24 c\u00e1i k\u1eb9o. An c\u00f3 nhi\u1ec1u h\u01a1n B\u00ecnh 6 c\u00e1i k\u1eb9o. H\u1ecfi m\u1ed7i b\u1ea1n c\u00f3 bao nhi\u00eau c\u00e1i k\u1eb9o?"},
    {"grade": "L\u1edbp 5", "topic": "To\u00e1n chuy\u1ec3n \u0111\u1ed9ng \u0111\u1ec1u", "prompt": "M\u1ed9t \u00f4 t\u00f4 \u0111i qu\u00e3ng \u0111\u01b0\u1eddng d\u00e0i 120 km trong th\u1eddi gian 2 gi\u1edd 30 ph\u00fat. H\u00e3y t\u00ednh v\u1eadn t\u1ed1c c\u1ee7a \u00f4 t\u00f4."},
]

ALL_GRADE_TESTS = [
    {"grade": "L\u1edbp 1", "topic": "Ph\u00e9p c\u1ed9ng trong ph\u1ea1m vi 20", "prompt": "C\u00f3 7 qu\u1ea3 t\u00e1o, th\u00eam 5 qu\u1ea3 t\u00e1o. H\u1ecfi c\u00f3 t\u1ea5t c\u1ea3 bao nhi\u00eau qu\u1ea3 t\u00e1o?"},
    *ELEMENTARY_TESTS,
]


def run_benchmark(
    model: Any,
    tokenizer: Any,
    config: AppConfig,
    output_path: Path | str | None = None,
    tests: list[dict[str, str]] | None = None,
) -> str:
    """Chay benchmark luot dau va tra ve bao cao Markdown."""
    rows = ["# K\u1ebft qu\u1ea3 \u0111\u00e1nh gi\u00e1 ph\u1ea3n h\u1ed3i g\u1ee3i m\u1edf", "", f"Th\u1eddi gian: {datetime.now().astimezone().isoformat(timespec='seconds')}", ""]
    for item in tests or ELEMENTARY_TESTS:
        response = run_pedagogical_inference(
            user_text=item["prompt"], system_prompt=CONCRETE_SOCRATIC_PROMPT,
            model=model, tokenizer=tokenizer, enable_thinking=False,
            max_new_tokens=300, temp=0.25, config=config,
        )
        rows.extend([f"## {item['grade']} - {item['topic']}", f"**\u0110\u1ec1 b\u00e0i:** {item['prompt']}", "", f"**Ph\u1ea3n h\u1ed3i g\u1ee3i m\u1edf:** {response}", "", "---", ""])
    report = "\n".join(rows)
    if output_path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(report, encoding="utf-8")
    return report
