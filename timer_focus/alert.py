from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from .core import load_config


def notify(title: str, body: str) -> None:
    cmd = shutil.which("notify-send")
    if not cmd:
        return
    subprocess.run([cmd, title, body], check=False)


def popup(title: str, body: str, timeout_sec: int) -> None:
    cmd = shutil.which("yad")
    if not cmd:
        return
    subprocess.Popen(
        [
            cmd,
            "--title",
            title,
            "--text",
            body,
            "--on-top",
            "--skip-taskbar",
            "--timeout",
            str(max(1, int(timeout_sec))),
            "--button=OK:0",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def play_sound_if_enabled() -> None:
    config = load_config()
    if not bool(config.get("enable_sound", True)):
        return

    canberra = shutil.which("canberra-gtk-play")
    if canberra:
        subprocess.Popen(
            [canberra, "-i", "complete"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return

    sound_file = Path("/usr/share/sounds/freedesktop/stereo/complete.oga")
    for player in ("pw-play", "paplay"):
        cmd = shutil.which(player)
        if cmd and sound_file.exists():
            subprocess.Popen(
                [cmd, str(sound_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="pomodoro-alert")
    parser.add_argument("--event", default="work_done")
    parser.add_argument("--next", default="work")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()

    if args.event == "work_done":
        title = "Pomodoro Done"
        body = f"Take a break. Next: {args.next.replace('_', ' ')}"
    else:
        title = "Break Done"
        body = "Back to focus."

    notify(title, body)
    popup(title, body, int(config.get("popup_timeout_sec", 20)))
    play_sound_if_enabled()


if __name__ == "__main__":
    main()
