#!/usr/bin/env python3
import asyncio
import io
import json
import os
import sys
from datetime import datetime

import websockets
from vncdotool import api as vncapi

from mcp.server.fastmcp import FastMCP, Image

# Emulator display dimensions (the SDL2 window rendered on the virtual framebuffer)
EMULATOR_W = 412
EMULATOR_H = 552

WS_URL = "ws://localhost:9001"
MCP_PORT = int(os.environ.get("MCP_PORT", "9003"))

# Workaround for debug link & button request race conditions
# See: https://github.com/trezor/trezor-suite/issues/23270
EMU_INTERACTION_DELAY = 0.2

# Screenshots are saved to the container's /trezor-user-env/logs/mcp-screenshots
# which is typically volume-mounted to the host's logs/ directory
SCREENSHOT_DIR = os.path.join(
    os.environ.get("TREZOR_USER_ENV_WORK_DIR", "/trezor-user-env"),
    "logs",
    "mcp-screenshots",
)

mcp = FastMCP("trezor-emulator", host="0.0.0.0", port=MCP_PORT)


def log(text: str) -> None:
    print(f"MCP: {text}", file=sys.stderr, flush=True)


async def _send_command(payload: dict, timeout: float = 120) -> dict:
    """Send a command to the emulator WebSocket and return the response."""
    async with websockets.connect(WS_URL, open_timeout=10) as ws:
        await asyncio.wait_for(ws.recv(), timeout=10)  # consume welcome message
        await ws.send(json.dumps(payload))
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
        return json.loads(raw)


# ---------------------------------------------------------------------------
# Bridge tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def bridge_start(version: str = "node-bridge") -> str:
    """
    Start the Trezor bridge.

    Args:
        version: Bridge version to start. Options: "node-bridge" (default), "local-suite-node-bridge".
    """
    result = await _send_command({"type": "bridge-start", "version": version})
    if result.get("success"):
        return f"Bridge started: {result.get('response', 'ok')}"
    return f"Bridge start failed: {result}"


@mcp.tool()
async def bridge_stop() -> str:
    """Stop the Trezor bridge."""
    result = await _send_command({"type": "bridge-stop"})
    if result.get("success"):
        return "Bridge stopped"
    return f"Bridge stop failed: {result}"


# ---------------------------------------------------------------------------
# Emulator lifecycle tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def emulator_start(model: str, version: str = "", wipe: bool = False) -> str:
    """
    Start a Trezor emulator with the specified model and firmware version.

    Args:
        model: Trezor model to emulate. One of: "T1B1" (Trezor One), "T2T1" (Trezor T), "T3B1" (Safe 3), "T3T1" (Safe 5), "T3W1" (Safe 7).
        version: Firmware version (e.g. "2.7.1"). Empty string or omit for latest development build. Use "-latest" suffix for latest release.
        wipe: Whether to wipe device storage on start.
    """
    payload: dict = {"type": "emulator-start", "model": model, "wipe": wipe}
    if version:
        payload["version"] = version
    result = await _send_command(payload)
    if result.get("success"):
        return f"Emulator started: {result.get('response', 'ok')}"
    return f"Emulator start failed: {result}"


@mcp.tool()
async def emulator_start_from_url(url: str, model: str, wipe: bool = False) -> str:
    """
    Download and start a Trezor emulator from a firmware URL.

    Args:
        url: URL to download the emulator firmware binary from.
        model: Trezor model. One of: "T1B1", "T2T1", "T3B1", "T3T1", "T3W1".
        wipe: Whether to wipe device storage on start.
    """
    result = await _send_command(
        {"type": "emulator-start-from-url", "url": url, "model": model, "wipe": wipe}
    )
    if result.get("success"):
        return f"Emulator started from URL: {result.get('response', 'ok')}"
    return f"Emulator start from URL failed: {result}"


@mcp.tool()
async def emulator_start_from_branch(
    branch: str, model: str, btc_only: bool = False, wipe: bool = False
) -> str:
    """
    Download and start a Trezor emulator built from a specific git branch.

    Args:
        branch: Git branch name (e.g. "main", "feature/xyz").
        model: Trezor model. One of: "T1B1", "T2T1", "T3B1", "T3T1", "T3W1".
        btc_only: Use Bitcoin-only firmware build.
        wipe: Whether to wipe device storage on start.
    """
    result = await _send_command(
        {
            "type": "emulator-start-from-branch",
            "branch": branch,
            "model": model,
            "btc_only": btc_only,
            "wipe": wipe,
        }
    )
    if result.get("success"):
        return f"Emulator started from branch: {result.get('response', 'ok')}"
    return f"Emulator start from branch failed: {result}"


@mcp.tool()
async def emulator_stop() -> str:
    """Stop the Trezor emulator."""
    result = await _send_command({"type": "emulator-stop"})
    return f"Stop result: {result}"


# ---------------------------------------------------------------------------
# Device setup tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def emulator_setup(
    mnemonic: str,
    pin: str,
    passphrase_protection: bool,
    label: str,
    needs_backup: bool = False,
) -> str:
    """
    Set up the Trezor emulator with a seed phrase and device settings.

    Args:
        mnemonic: BIP39 mnemonic seed phrase (e.g. "all all all all all all all all all all all all").
        pin: PIN code for the device (empty string for no PIN).
        passphrase_protection: Whether to enable passphrase protection.
        label: Device label.
        needs_backup: Whether device should be marked as needing backup.
    """
    # Stop bridge before setup to avoid 'wrong previous session' errors.
    await _send_command({"type": "bridge-stop"})
    result = await _send_command(
        {
            "type": "emulator-setup",
            "mnemonic": mnemonic,
            "pin": pin,
            "passphrase_protection": passphrase_protection,
            "label": label,
            "needs_backup": needs_backup,
        }
    )
    if result.get("success"):
        return f"Emulator set up: {result.get('response', 'ok')}"
    return f"Emulator setup failed: {result}"


@mcp.tool()
async def emulator_wipe() -> str:
    """Wipe the Trezor emulator device (removes all data including seed)."""
    result = await _send_command({"type": "emulator-wipe"})
    if result.get("success"):
        return "Device wiped"
    return f"Wipe failed: {result}"


@mcp.tool()
async def emulator_apply_settings(
    label: str = "",
    passphrase_always_on_device: bool = False,
    auto_lock_delay_ms: int = 0,
) -> str:
    """
    Apply settings to the Trezor emulator device.

    Args:
        label: Device label to display. Empty string to leave unchanged.
        passphrase_always_on_device: Whether passphrase should always be entered on device.
        auto_lock_delay_ms: Auto-lock delay in milliseconds. 0 to leave unchanged.
    """
    payload: dict = {"type": "emulator-apply-settings"}
    if label:
        payload["label"] = label
    if passphrase_always_on_device:
        payload["passphrase_always_on_device"] = passphrase_always_on_device
    if auto_lock_delay_ms:
        payload["auto_lock_delay_ms"] = auto_lock_delay_ms
    result = await _send_command(payload)
    if result.get("success"):
        return f"Settings applied: {result.get('response', 'ok')}"
    return f"Apply settings failed: {result}"


# ---------------------------------------------------------------------------
# Interaction tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def emulator_click(x: int, y: int) -> str:
    """
    Touch (click) a coordinate on the Trezor emulator display.

    The display is 412x552 pixels: (0,0) is top-left, (411,551) is bottom-right.

    Common button positions on the THP pairing screen:
      - Confirm / green checkmark: x=255, y=491
      - Dismiss / X button:        x=88,  y=491
    """
    await asyncio.sleep(EMU_INTERACTION_DELAY)
    result = await _send_command({"type": "emulator-click", "x": x, "y": y})
    if result.get("success"):
        return f"Clicked at ({x}, {y}): {result.get('response', 'ok')}"
    return f"Click failed: {result}"


@mcp.tool()
async def emulator_swipe(direction: str) -> str:
    """
    Swipe on the Trezor emulator touchscreen.

    Args:
        direction: Swipe direction - one of "up", "down", "left", "right".
    """
    await asyncio.sleep(EMU_INTERACTION_DELAY)
    result = await _send_command({"type": "emulator-swipe", "direction": direction})
    if result.get("success"):
        return f"Swiped {direction}"
    return f"Swipe failed: {result}"


@mcp.tool()
async def emulator_press_yes() -> str:
    """Press the physical YES (confirm) button on the Trezor emulator."""
    await asyncio.sleep(EMU_INTERACTION_DELAY)
    result = await _send_command({"type": "emulator-press-yes"})
    if result.get("success"):
        return "Pressed YES"
    return f"Press YES failed: {result}"


@mcp.tool()
async def emulator_press_no() -> str:
    """Press the physical NO (cancel) button on the Trezor emulator."""
    await asyncio.sleep(EMU_INTERACTION_DELAY)
    result = await _send_command({"type": "emulator-press-no"})
    if result.get("success"):
        return "Pressed NO"
    return f"Press NO failed: {result}"


@mcp.tool()
async def emulator_input(value: str) -> str:
    """Type text into the Trezor emulator (e.g. PIN or passphrase)."""
    await asyncio.sleep(EMU_INTERACTION_DELAY)
    result = await _send_command({"type": "emulator-input", "value": value})
    if result.get("success"):
        return f"Typed input: {value!r}"
    return f"Input failed: {result}"


# ---------------------------------------------------------------------------
# Diagnostics tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def emulator_get_features() -> str:
    """Get the current features/capabilities of the Trezor emulator device."""
    result = await _send_command({"type": "emulator-get-features"})
    if result.get("success"):
        return json.dumps(result.get("response", {}), indent=2)
    return f"Get features failed: {result}"


@mcp.tool()
async def emulator_get_debug_state() -> str:
    """Get the current debug state of the Trezor emulator (layout, PIN, mnemonic, etc.)."""
    await asyncio.sleep(EMU_INTERACTION_DELAY)
    result = await _send_command({"type": "emulator-get-debug-state"})
    if result.get("success"):
        return json.dumps(result.get("response", {}), indent=2)
    return f"Get debug state failed: {result}"


@mcp.tool()
async def background_check() -> str:
    """Check the status of all running services (bridge, emulator, regtest, tropic model server)."""
    result = await _send_command({"type": "background-check"})
    return json.dumps(
        {
            "bridge_status": result.get("bridge_status"),
            "emulator_status": result.get("emulator_status"),
            "regtest_status": result.get("regtest_status"),
            "tropic_status": result.get("tropic_status"),
        },
        indent=2,
    )


@mcp.tool()
async def emulator_screenshot() -> Image:
    """
    Take a screenshot of the Trezor emulator display and return it as a PNG image.

    Captures directly from the VNC server on port 5900.
    Screenshots are also saved to logs/mcp-screenshots/ for later reference.
    """
    try:
        client = vncapi.connect("localhost::5900")
        png_buffer = io.BytesIO()
        png_buffer.name = "screenshot.png"
        client.captureScreen(png_buffer)
        client.disconnect()
        png_data = png_buffer.getvalue()

        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filepath = os.path.join(SCREENSHOT_DIR, f"{timestamp}.png")
        with open(filepath, "wb") as f:
            f.write(png_data)
        # Match ownership to the bind-mounted logs dir so the host user owns
        # screenshots when we run as root in a container.
        dir_stat = os.stat(SCREENSHOT_DIR)
        os.chown(filepath, dir_stat.st_uid, dir_stat.st_gid)
        os.chmod(filepath, 0o644)

        return Image(data=png_data, format="png")
    except Exception as e:
        raise RuntimeError(
            f"VNC screenshot failed (ensure emulator VNC is running on localhost:5900): {e}"
        )


@mcp.tool()
async def emulator_ping() -> str:
    """Ping the emulator WebSocket server. Returns 'pong' if reachable."""
    result = await _send_command({"type": "ping"})
    return f"Ping result: {result}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "sse")
    if transport == "sse":
        log(f"Starting MCP server (SSE) on 0.0.0.0:{MCP_PORT}")
        mcp.run(transport="sse")
    else:
        log("Starting MCP server (stdio)")
        mcp.run()
