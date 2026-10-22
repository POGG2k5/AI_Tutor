"""Chat terminal with /reset, /mode 1|2|3 and /quit commands."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import configure_logging, load_config
from app.inference import MultiTurnMathSession
from app.model_loader import load_model
from app.prompts import MODE_KEYS, PROMPT_MODES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chatbot To\u00e1n ti\u1ec3u h\u1ecdc tr\u00ean terminal")
    parser.add_argument("--model", type=Path, help="\u0110\u01b0\u1eddng d\u1eabn checkpoint, ghi \u0111\u00e8 MODEL_PATH")
    parser.add_argument("--mode", choices=("socratic", "visual", "worked"), default="socratic")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging()
    config = load_config()
    if args.model:
        config = type(config)(**{**config.__dict__, "model_path": args.model.resolve()})
    model, tokenizer = load_model(config)
    mode = MODE_KEYS[args.mode]
    session = MultiTurnMathSession(model, tokenizer, PROMPT_MODES[mode], config)
    print("Nh\u1eadp /reset, /mode 1|2|3 ho\u1eb7c /quit.")
    while True:
        try:
            user_text = input("Em: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_text:
            continue
        if user_text == "/quit":
            break
        if user_text == "/reset":
            session.reset()
            print("\u0110\u00e3 l\u00e0m m\u1edbi h\u1ed9i tho\u1ea1i.")
            continue
        if user_text.startswith("/mode "):
            selected = {"1": "socratic", "2": "visual", "3": "worked"}.get(user_text.split(maxsplit=1)[1])
            if selected is None:
                print("D\u00f9ng /mode 1, /mode 2 ho\u1eb7c /mode 3.")
            else:
                session.reset(PROMPT_MODES[MODE_KEYS[selected]])
                print("\u0110\u00e3 \u0111\u1ed5i ch\u1ebf \u0111\u1ed9 v\u00e0 l\u00e0m m\u1edbi h\u1ed9i tho\u1ea1i.")
            continue
        print(f"Gia s\u01b0 AI: {session.send_message(user_text)}")


if __name__ == "__main__":
    main()
