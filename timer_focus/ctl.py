from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

from .core import (
    LOCK_PATH,
    default_state,
    load_config,
    load_state,
    mode_minutes,
    now_ts,
    running_remaining,
    start_state,
    transition_on_completion,
    write_state,
)


def humanize_remaining(seconds: int) -> str:
    seconds = max(0, int(seconds))
    if seconds <= 0:
        return "0m"
    total_minutes = (seconds + 59) // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours > 0 and minutes > 0:
        return f"{hours}h {minutes}m"
    if hours > 0:
        return f"{hours}h"
    return f"{total_minutes}m"


def daemon_running() -> bool:
    if not LOCK_PATH.exists():
        return False
    try:
        result = subprocess.run(
            ["pgrep", "-f", r"timer_focus\.daemon"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def ensure_daemon_running() -> None:
    if daemon_running():
        return
    subprocess.Popen(
        [sys.executable, "-m", "timer_focus.daemon"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    time.sleep(0.1)


def do_start(minutes: int | None) -> int:
    ensure_daemon_running()
    config = load_config()
    if minutes is None:
        minutes = mode_minutes("work", config)
    state = load_state()
    updated = start_state("work", minutes, base_state=state)
    write_state(updated)
    return 0


def do_pause() -> int:
    state = load_state()
    if state.get("status") != "running":
        return 1
    now = now_ts()
    remain = max(0, int(state.get("ends_at", 0)) - now)
    state["status"] = "paused"
    state["remaining_sec"] = remain
    state["ends_at"] = now
    write_state(state)
    return 0


def do_resume() -> int:
    ensure_daemon_running()
    state = load_state()
    if state.get("status") != "paused":
        return 1
    now = now_ts()
    remain = max(1, int(state.get("remaining_sec", 0)))
    state["status"] = "running"
    state["started_at"] = now
    state["ends_at"] = now + remain
    write_state(state)
    return 0


def do_stop() -> int:
    state = load_state()
    state.update(
        {
            "mode": "work",
            "status": "idle",
            "started_at": 0,
            "ends_at": 0,
            "remaining_sec": 0,
        }
    )
    write_state(state)
    return 0


def do_reset() -> int:
    write_state(default_state())
    return 0


def do_skip() -> int:
    state = load_state()
    if state.get("status") not in {"running", "paused"}:
        return 1
    state["ends_at"] = now_ts() - 1
    state["status"] = "running"
    write_state(state)
    return 0


def do_status(as_json: bool) -> int:
    state = load_state()
    if state.get("status") == "running" and now_ts() >= int(state.get("ends_at", 0)):
        config = load_config()
        event, next_mode, updated = transition_on_completion(state, config)
        write_state(updated)
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "timer_focus.alert",
                "--event",
                event,
                "--next",
                next_mode,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        state = updated
    remaining = running_remaining(state)
    state["remaining_sec"] = remaining
    state["remaining_human"] = humanize_remaining(remaining)
    if as_json:
        print(json.dumps(state, ensure_ascii=True))
        return 0
    print(
        f"status={state['status']} mode={state['mode']} remaining={state['remaining_human']} ({state['remaining_sec']}s) "
        f"cycle_index={state['cycle_index']} today_completed={state['today_completed']}"
    )
    return 0


def do_toggle() -> int:
    if do_pause() == 0:
        return 0
    return do_resume()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="pomodoroctl")
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start")
    p_start.add_argument("minutes", type=int, nargs="?")

    sub.add_parser("pause")
    sub.add_parser("resume")
    sub.add_parser("stop")
    sub.add_parser("reset")
    sub.add_parser("skip")
    sub.add_parser("toggle")

    p_status = sub.add_parser("status")
    p_status.add_argument("--json", action="store_true")

    sub.add_parser("daemon")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cmd = args.command
    if cmd == "start":
        code = do_start(args.minutes)
    elif cmd == "pause":
        code = do_pause()
    elif cmd == "resume":
        code = do_resume()
    elif cmd == "stop":
        code = do_stop()
    elif cmd == "reset":
        code = do_reset()
    elif cmd == "skip":
        code = do_skip()
    elif cmd == "toggle":
        code = do_toggle()
    elif cmd == "status":
        code = do_status(args.json)
    elif cmd == "daemon":
        ensure_daemon_running()
        result = subprocess.run(
            ["pgrep", "-f", r"timer_focus\.daemon"],
            check=False,
            capture_output=True,
            text=True,
        )
        first_pid = result.stdout.strip().splitlines()[0] if result.stdout else ""
        if first_pid:
            print(first_pid)
        code = 0
    else:
        code = 2
    raise SystemExit(code)


if __name__ == "__main__":
    main()
