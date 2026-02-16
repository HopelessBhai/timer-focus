from __future__ import annotations

import argparse
import fcntl
import subprocess
import sys
import time

from .core import (
    LOCK_PATH,
    ensure_dirs,
    load_config,
    load_state,
    now_ts,
    transition_on_completion,
    write_state,
)


def launch_alert(event: str, next_mode: str) -> None:
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


def run_daemon() -> None:
    ensure_dirs()
    lock_file = LOCK_PATH.open("w", encoding="utf-8")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("pomodoro-daemon is already running", file=sys.stderr)
        sys.exit(1)

    while True:
        state = load_state()
        if state.get("status") == "running":
            now = now_ts()
            if now >= int(state.get("ends_at", 0)):
                config = load_config()
                event, next_mode, updated = transition_on_completion(state, config)
                write_state(updated)
                launch_alert(event, next_mode)
        time.sleep(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="pomodoro-daemon")
    return parser.parse_args()


def main() -> None:
    parse_args()
    run_daemon()


if __name__ == "__main__":
    main()
