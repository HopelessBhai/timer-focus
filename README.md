# timer-focus

Minimal Pomodoro timer for Linux/Waybar setups (Omarchy-friendly).

It provides a background daemon, CLI controls, live Waybar output, and end-of-session alerts with popup + notification. The goal is a fast, dependency-light focus timer that is easy to run from terminal and easy to integrate into desktop workflows.


Pomodoro commands:
- `pomodoro` (alias command; supports all subcommands)
- `pomodoro-daemon` (background session engine)
- `pomodoroctl` (CLI controls)
- `pomodoro-waybar` (Waybar JSON output)
- `pomodoro-alert` (popup + notification + optional sound)

## Install

```bash
uv sync
uv tool install --from . timer-focus
```

## Commands

```bash
pomodoro-daemon
pomodoroctl start 25
pomodoroctl pause
pomodoroctl resume
pomodoroctl stop
pomodoroctl reset
pomodoroctl skip
pomodoroctl status
pomodoroctl status --json
pomodoro reset
```

`pomodoroctl status` shows human time + seconds, for example:

```text
status=running mode=work remaining=16m (901s) cycle_index=0 today_completed=0
```

`pomodoroctl status --json` includes:

```json
{"remaining_sec": 901, "remaining_human": "16m"}
```

`pomodoroctl reset` (or `pomodoro reset`) resets all timer stats and forces idle state.
After every PC reboot, timer state is also reset to idle and stats are reset automatically.

## Waybar module

Add to your Waybar config:

```json
"custom/pomodoro": {
  "exec": "/home/atmadipg/.local/bin/pomodoro-waybar",
  "interval": 1,
  "return-type": "json",
  "on-click": "/home/atmadipg/.local/bin/pomodoroctl toggle",
  "on-click-right": "/home/atmadipg/.local/bin/pomodoroctl stop",
  "tooltip": true
}
```

Also add `custom/pomodoro` to one of your bar module lists (for example `modules-right`).

Run daemon:

```bash
/home/atmadipg/.local/bin/pomodoro-daemon &
pkill -SIGUSR2 waybar
waybar &
```

## Config

Auto-created at:
- `~/.config/pomodoro/config.toml`

Defaults:

```toml
work_minutes = 25
short_break_minutes = 5
long_break_minutes = 15
long_break_every = 4
popup_timeout_sec = 20
enable_sound = true
```

## Runtime state

- `~/.local/state/pomodoro/state.json`
- `~/.local/state/pomodoro/daemon.lock`
