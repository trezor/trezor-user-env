# Controller

## General information
- Always up-to-date info with all the implementation details can be found in **src/controller.py**.
- Controller runs on port 9001.
- Requests must be in JSON structure, command is specified in the `type` key, e.g. `{"type": "ping"}`.
- All arguments (if needed) need to be specified in the same root JSON, e.g. `{"type": "emulator-start", "version": "2.4.0"}`.
- It is beneficial to always include `id` integer in the request, as it is being sent back in the response, and these two can be matched.
- Response is always in JSON format, includes boolean `success` key, indicating if everything went as expected, e.g. `{"success": False, "error": "Unknown command - xyz"}`.
- Response contains a confirmation of what happened in the `response` key, e.g. `{"success": True, "response": "Emulator 2.4.0. started"}`.

## Supported commands

- **ping**
  - **response**: `{"response": "pong"}`

- **log**
  - **action**: log the supplied text to be preserved in debugging.log (e.g. for auditing purposes)
  - **arguments**:
    - **text**: `str`

- **background-check**
  - **action**: check current status of bridge and emulator
  - **response**: `{"bridge_status": bool, "emulator_status": bool}`

- **emulator-start**
  - **action**: start the specified version of emulator (and if one already runs, kills it)
  - **arguments**:
    - **version**: `str` (1.9.4, 2.4.0., etc.) - default is the latest TT
    - **wipe**: `bool` (default=False) whether to delete the emulator profile before starting it
    - **output_to_logfile**: `bool` (default=True) whether the debug output should go to a logfile - otherwise it goes to stdout
    - **save_screenshots**: `bool` (default=False) whether to save screenshots to enable calling **emulator-get-screenshot**

- **emulator-start-from-url**
  - **action**: downloads emulator from specified URL and runs it
  - **arguments**:
    - **url**: `str` from where to download the emulator
    - **model**: `str` which emulator it is - either "1" for T1 or "2" for T2
    - **wipe**: `bool` (default=False) whether to delete the emulator profile before starting it
    - **output_to_logfile**: `bool` (default=True) whether the debug output should go to a logfile - otherwise it goes to stdout
    - **save_screenshots**: `bool` (default=False) whether to save screenshots to enable calling **emulator-get-screenshot**

- **emulator-stop**
  - **action**: stop the emulator

- **emulator-setup**
  - **action**: perform the emulator setup
  - **arguments**:
    - all appropriate to the `load_device()` function in `trezorlib`
    - **mnemonic**: `str`
    - **pin**: `str`
    - **passphrase_protection**: `bool`
    - **label**: `str`
    - **needs_backup**: `bool` (default=False)

- **emulator-press-yes**
  - **action**: press yes button on the emulator

- **emulator-press-no**
  - **action**: press no button on the emulator

- **emulator-input**
  - **action**: enter a string into a field on the emulator (such as passphrase entry)
  - **arguments**:
    - **value**: `str`

- **emulator-click**
  - **action**: click on a specified pixel coordination (x, y) on emulator
  - **arguments**:
    - **x**: `int`
    - **y**: `int`

- **emulator-read-and-confirm-mnemonic**
  - **action**: simulates the Single backup process

- **emulator-read-and-confirm-shamir-mnemonic**
  - **action**: simulates the Shamir backup process for chosen amount of shares and threshold
  - **arguments**:
    - **shares**: `int` (default=1)
    - **threshold**: `int` (default=1)

- **emulator-allow-unsafe-paths**
  - **action**: allow unsafe path on emulator

- **select-num-of-words**
  - **action**: set the number of seed words
  - **arguments**:
    - **num**: `int`

- **emulator-swipe**
  - **action**: peform swipe on the device
  - **arguments**:
    - **direction**: `str` ("up", "down", "right", "left")

- **emulator-wipe**
  - **action**: wipe the emulator

- **emulator-apply-settings**
  - **action**: apply settings on emulator
  - **arguments**:
    - all appropriate to the `apply_settings()` function in `trezorlib` (all of them are optional)
    - **language**: `str`
    - **label**: `str`
    - **use_passphrase**: `bool`
    - **homescreen**: `str`
    - **auto_lock_delay_ms**: `int`
    - **display_rotation**: `int`
    - **passphrase_always_on_device**: `bool`
    - **safety_checks**: `int`

- **emulator-reset-device**
  - **action**: reset the device
  - **arguments**:
    - **use_shamir**: `bool` (optional) - whether to use Shamir backup (SLIP39) - default is False (BIP39 will be used)


- **emulator-get-screenshot**
  - **action**: get current screen encoded as base64
  - **response**: `{"response": str}`

- **bridge-start**
  - **action**: start the specified version of bridge (only if it is not already running)
  - **arguments**:
    - **version**: `str` (2.0.27, 2.0.31, etc.) - defaults to the latest available one
    - **output_to_logfile**: `bool` (default=True) whether the debug output should go to a logfile, otherwise it goes to stdout

- **bridge-stop**
  - **action**: stop the bridge

- **regtest-mine-blocks**
  - **action**: mine amount of blocks, optionally to a specified address
  - **arguments**:
    - **block_amount**: `int`
    - **address**: `str` (optional) - defaults to the wallet's own address

- **regtest-send-to-address**
  - **action**: send amount of BTC to address (also mines a new block to confirm the transaction)
  - **arguments**:
    - **btc_amount**: `float`
    - **address**: `str`

- **exit**
  - **action**: stop the controller
