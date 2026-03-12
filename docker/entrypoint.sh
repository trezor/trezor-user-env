#!/bin/bash
# entrypoint.sh — Start a virtual X11 display (Xvfb) + VNC + noVNC web viewer,
# then exec the main application command.
#
# This allows the Trezor emulator SDL2 window to be viewed in a browser at
# http://localhost:6080/vnc.html without requiring X11 or XQuartz on the host.

set -e

DISPLAY_NUM=":69"
VNC_PORT=5900
NOVNC_PORT=6080
SCREEN_RES="2048x2048x24"

echo "[entrypoint] Starting Xvfb virtual display on ${DISPLAY_NUM} (${SCREEN_RES})..."
Xvfb "${DISPLAY_NUM}" -screen 0 "${SCREEN_RES}" -ac +extension GLX +render -noreset &
XVFB_PID=$!

export DISPLAY="${DISPLAY_NUM}"

# Wait until Xvfb responds
for i in $(seq 1 20); do
    if xdpyinfo -display "${DISPLAY_NUM}" >/dev/null 2>&1; then
        echo "[entrypoint] Xvfb ready after ${i} second(s)."
        break
    fi
    if [ "$i" -eq 20 ]; then
        echo "[entrypoint] ERROR: Xvfb did not start in time." >&2
        exit 1
    fi
    sleep 0.5
done

echo "[entrypoint] Starting noVNC web proxy on port ${NOVNC_PORT}..."
websockify \
    --web /usr/share/novnc \
    "${NOVNC_PORT}" \
    "localhost:${VNC_PORT}" \
    &>/dev/null &

# Function to start x11vnc
start_vnc() {
    local target="$1"
    pkill -9 x11vnc || true
    sleep 0.5
    echo "[vnc] Starting x11vnc targeting: $target"
    if [ "$target" = "root" ]; then
        x11vnc -display "${DISPLAY_NUM}" -nopw -rfbport "${VNC_PORT}" -forever -shared -quiet &
    else
        x11vnc -display "${DISPLAY_NUM}" -nopw -rfbport "${VNC_PORT}" -forever -shared -quiet -id "$target" &
    fi
}

# Initial start on root window
start_vnc "root"

# Window Watcher / RemoteApp logic:
# It waits for the emulator window, finds its ID, and attaches x11vnc to it.
(
    last_state="root"
    while true; do
        # Search for any window that is NOT the root window (id != 0x...)
        # Emulator usually has "trezor" or "SDL" in class or name
        win_id=$(xdotool search --onlyvisible --name "Trezor" 2>/dev/null | tail -n1)
        if [ -z "$win_id" ]; then
            win_id=$(xdotool search --onlyvisible --class "SDL" 2>/dev/null | tail -n1)
        fi
        
        current_state="root"
        [ -n "$win_id" ] && current_state="$win_id"

        if [ "$current_state" != "$last_state" ]; then
            echo "[watcher] State change: $last_state -> $current_state"
            start_vnc "$current_state"
            last_state="$current_state"
        fi
        sleep 1
    done
) &

echo "[entrypoint] Emulator RemoteApp watcher started."
echo "[entrypoint] Executing: $*"
exec "$@"
