from __future__ import annotations

import json

from .core import format_mmss, load_state, running_remaining, title_mode

ICONS = {
    "work": "🍅",
    "short_break": "☕",
    "long_break": "🌿",
}


def build_payload() -> dict:
    state = load_state()
    status = state.get("status", "idle")
    mode = state.get("mode", "work")
    icon = ICONS.get(mode, "🍅")

    if status == "idle":
        return {
            "text": f"{icon} --:--",
            "class": "idle",
            "tooltip": "Pomodoro idle",
        }

    remaining = running_remaining(state)
    text = f"{icon} {format_mmss(remaining)}"
    tooltip = (
        f"{title_mode(mode)} | status: {status} | "
        f"cycle: {int(state.get('cycle_index', 0))} | "
        f"completed today: {int(state.get('today_completed', 0))}"
    )
    return {
        "text": text,
        "class": f"{status} {mode}",
        "tooltip": tooltip,
    }


def main() -> None:
    payload = build_payload()
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
