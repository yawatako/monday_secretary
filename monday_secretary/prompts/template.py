from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


RULES_PATH = Path(__file__).with_name("rules.yml")


def build_prompt(user_msg: str, context: Dict[str, Any]) -> str:
    """Merge rules, context and user message into a single prompt string."""
    with open(RULES_PATH, encoding="utf-8") as f:
        rules_text = f.read()

    context_text = json.dumps(context, ensure_ascii=False, indent=2)

    parts = [
        rules_text,
        "\n<CONTEXT>\n",
        context_text,
        "\n</CONTEXT>\n",
        user_msg,
    ]
    return "\n".join(parts)
