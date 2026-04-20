# MCP Server

## General information

- The MCP (Model Context Protocol) server allows AI assistants like Claude Code to control the Trezor emulator programmatically.
- It runs on port **9003** using SSE (Server-Sent Events) transport.
- It acts as a thin wrapper over the [Controller](controller.md) WebSocket API on port 9001 and the VNC server on port 5900.
- The MCP server runs in its own `uv`-managed virtual environment (`src/mcp/`) because it requires `pydantic>=2`, which conflicts with the `tvl` dependency in the main project.
- It starts automatically alongside the other services when the container launches.
- Source code: `src/mcp/server.py`

## Connecting Claude Code

Add the following to your project's `.mcp.json` (or use `claude mcp add`):

```json
{
  "mcpServers": {
    "trezor-emulator": {
      "type": "sse",
      "url": "http://localhost:9003/sse"
    }
  }
}
```

Or via CLI:

```bash
claude mcp add --transport sse trezor-emulator http://localhost:9003/sse
```

Once connected, the tools will be available to Claude Code automatically.

## Available tools

### Bridge management

- **bridge_start** - Start the Trezor bridge
  - `version`: `str` (default: `"node-bridge"`) - options: `"node-bridge"`, `"local-suite-node-bridge"`, `"2.0.33"`, `"2.0.32"`
- **bridge_stop** - Stop the Trezor bridge

### Emulator lifecycle

- **emulator_start** - Start an emulator with a specific model and firmware version
  - `model`: `str` - one of `"T1B1"`, `"T2T1"`, `"T3B1"`, `"T3T1"`, `"T3W1"`
  - `version`: `str` (default: `""` for latest dev build) - e.g. `"2.7.1"`, `"-latest"` for latest release
  - `wipe`: `bool` (default: `false`)
- **emulator_start_from_url** - Start an emulator from a firmware binary URL
  - `url`: `str`, `model`: `str`, `wipe`: `bool`
- **emulator_start_from_branch** - Start an emulator built from a git branch
  - `branch`: `str`, `model`: `str`, `btc_only`: `bool`, `wipe`: `bool`
- **emulator_stop** - Stop the running emulator

### Device setup

- **emulator_setup** - Load a seed phrase and configure the device
  - `mnemonic`: `str` - BIP39 seed phrase (e.g. `"all all all all all all all all all all all all"`)
  - `pin`: `str` - PIN code (empty string for no PIN)
  - `passphrase_protection`: `bool`
  - `label`: `str` - device label
  - `needs_backup`: `bool` (default: `false`)
- **emulator_wipe** - Wipe all data from the device
- **emulator_apply_settings** - Change device settings (label, passphrase, auto-lock)

### Interaction

- **emulator_click** - Touch a coordinate on the display (412x552 pixels)
  - `x`: `int`, `y`: `int`
- **emulator_swipe** - Swipe on the touchscreen
  - `direction`: `str` - one of `"up"`, `"down"`, `"left"`, `"right"`
- **emulator_press_yes** - Press the physical YES/confirm button
- **emulator_press_no** - Press the physical NO/cancel button
- **emulator_input** - Type text (PIN, passphrase)
  - `value`: `str`

### Diagnostics

- **emulator_get_features** - Get device features/capabilities
- **emulator_get_debug_state** - Get debug state (layout, PIN, mnemonic, etc.)
- **background_check** - Check status of all services (bridge, emulator, regtest, tropic)
- **emulator_screenshot** - Capture the emulator display as a PNG image (via VNC)
- **emulator_ping** - Check if the WebSocket server is reachable

## Architecture

```
MCP client (Claude Code)
    |
    | SSE (port 9003)
    v
src/mcp/server.py (FastMCP)
    |
    |--- WebSocket (port 9001) ---> controller.py ---> emulator / bridge
    |
    |--- VNC (port 5900) ---------> x11vnc ---------> screenshots
```
