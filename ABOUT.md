# About timer-focus

`timer-focus` is a Pomodoro timer built for Linux desktops using Waybar. It runs as a small daemon, exposes CLI commands to control sessions, prints Waybar-friendly JSON for live countdown display, and triggers notifications/popups when sessions end.

Designed for Omarchy-style workflows:
- quick terminal control (`start`, `pause`, `resume`, `stop`, `status`)
- persistent timer state in XDG config/state paths
- simple Waybar integration with click actions
- lightweight alerting via `notify-send` and `yad`

GitHub About (one-line):

Pomodoro timer for Waybar with daemon sessions, CLI control, live countdown, and popup alerts.
