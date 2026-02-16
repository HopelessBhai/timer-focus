from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import tomllib

CONFIG_ROOT = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
STATE_ROOT = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state")))
CONFIG_DIR = CONFIG_ROOT / "pomodoro"
STATE_DIR = STATE_ROOT / "pomodoro"
CONFIG_PATH = CONFIG_DIR / "config.toml"
STATE_PATH = STATE_DIR / "state.json"
LOCK_PATH = STATE_DIR / "daemon.lock"

DEFAULT_CONFIG: dict[str, Any] = {
    "work_minutes": 25,
    "short_break_minutes": 5,
    "long_break_minutes": 15,
    "long_break_every": 4,
    "popup_timeout_sec": 20,
    "enable_sound": True,
}


def ensure_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def maybe_write_default_config() -> None:
    ensure_dirs()
    if CONFIG_PATH.exists():
        return
    lines = []
    for key, value in DEFAULT_CONFIG.items():
        if isinstance(value, bool):
            lines.append(f"{key} = {'true' if value else 'false'}")
        else:
            lines.append(f"{key} = {value}")
    CONFIG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_config() -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    maybe_write_default_config()
    if not CONFIG_PATH.exists():
        return config
    try:
        parsed = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return config
    for key, default in DEFAULT_CONFIG.items():
        if key not in parsed:
            continue
        if isinstance(default, bool):
            config[key] = bool(parsed[key])
        else:
            try:
                config[key] = int(parsed[key])
            except (TypeError, ValueError):
                pass
    return config


def default_state() -> dict[str, Any]:
    return {
        "mode": "work",
        "status": "idle",
        "started_at": 0,
        "ends_at": 0,
        "remaining_sec": 0,
        "cycle_index": 0,
        "today_completed": 0,
    }


def load_state() -> dict[str, Any]:
    ensure_dirs()
    if not STATE_PATH.exists():
        return default_state()
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return default_state()
    state = default_state()
    state.update(data if isinstance(data, dict) else {})
    for key in ("started_at", "ends_at", "remaining_sec", "cycle_index", "today_completed"):
        try:
            state[key] = int(state.get(key, 0))
        except (TypeError, ValueError):
            state[key] = 0
    state["mode"] = str(state.get("mode", "work"))
    state["status"] = str(state.get("status", "idle"))
    return state


def write_state(state: dict[str, Any]) -> None:
    ensure_dirs()
    payload = json.dumps(state, ensure_ascii=True, separators=(",", ":"))
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(STATE_DIR),
        delete=False,
    ) as tmp:
        tmp.write(payload)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    tmp_path.replace(STATE_PATH)


def now_ts() -> int:
    return int(time.time())


def running_remaining(state: dict[str, Any], now: int | None = None) -> int:
    if now is None:
        now = now_ts()
    status = state.get("status")
    if status == "running":
        return max(0, int(state.get("ends_at", 0)) - now)
    if status == "paused":
        return max(0, int(state.get("remaining_sec", 0)))
    return 0


def mode_minutes(mode: str, config: dict[str, Any]) -> int:
    if mode == "short_break":
        return int(config["short_break_minutes"])
    if mode == "long_break":
        return int(config["long_break_minutes"])
    return int(config["work_minutes"])


def title_mode(mode: str) -> str:
    if mode == "short_break":
        return "Short Break"
    if mode == "long_break":
        return "Long Break"
    return "Work"


def format_mmss(seconds: int) -> str:
    seconds = max(0, int(seconds))
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"


def start_state(mode: str, minutes: int, base_state: dict[str, Any] | None = None) -> dict[str, Any]:
    if base_state is None:
        base_state = default_state()
    now = now_ts()
    total = max(1, int(minutes)) * 60
    next_state = dict(base_state)
    next_state.update(
        {
            "mode": mode,
            "status": "running",
            "started_at": now,
            "ends_at": now + total,
            "remaining_sec": total,
        }
    )
    return next_state


def idle_state(base_state: dict[str, Any] | None = None) -> dict[str, Any]:
    if base_state is None:
        base_state = default_state()
    next_state = dict(base_state)
    next_state.update(
        {
            "mode": "work",
            "status": "idle",
            "started_at": 0,
            "ends_at": 0,
            "remaining_sec": 0,
        }
    )
    return next_state


def transition_on_completion(state: dict[str, Any], config: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    completed = int(state.get("today_completed", 0))
    cycle_index = int(state.get("cycle_index", 0))
    current_mode = str(state.get("mode", "work"))

    if current_mode == "work":
        completed += 1
        cycle_index += 1
        interval = max(1, int(config.get("long_break_every", 4)))
        if cycle_index % interval == 0:
            next_mode = "long_break"
        else:
            next_mode = "short_break"
    else:
        next_mode = "work"

    next_state = dict(state)
    next_state["today_completed"] = completed
    next_state["cycle_index"] = cycle_index
    next_state = start_state(next_mode, mode_minutes(next_mode, config), base_state=next_state)
    return f"{current_mode}_done", next_mode, next_state
