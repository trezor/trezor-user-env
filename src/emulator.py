import os
import signal
import time
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Optional

from trezorlib import debuglink, device  # type: ignore
from trezorlib.debuglink import DebugLink  # type: ignore
from trezorlib.debuglink import TrezorClientDebugLink
from trezorlib.device import reset, wipe  # type: ignore
from trezorlib.transport.bridge import BridgeTransport  # type: ignore
from trezorlib.transport.udp import UdpTransport  # type: ignore

import bridge
import helpers

# TODO: consider creating a class from this module to avoid these globals
proc = None
version_running = None

ROOT_DIR = Path(__file__).parent.parent.resolve()

# When communicating with device via bridge/debuglink, this sleep is required
#   otherwise there may appear weird race conditions in communications.
# When not going through bridge but webusb, there is no need for it,
#   but we can skip bridge only when doing initial setup before test.
SLEEP = 0.501

# makes Trezor One emulator larger
TREZOR_ONE_OLED_SCALE = 2

LOG_COLOR = "magenta"


def log(text: str, color: str = LOG_COLOR) -> None:
    helpers.log(f"EMULATOR: {text}", color)


def get_bridge_device() -> device:
    devices = BridgeTransport.enumerate()
    for d in devices:
        d.find_debug()
        return d
    raise RuntimeError("No debuggable bridge device found")


def wait_for_bridge_device() -> device:
    start = time.monotonic()
    timeout = 15
    while True:
        try:
            device = get_bridge_device()
            return device
        except RuntimeError:
            elapsed = time.monotonic() - start
            if elapsed >= timeout:
                raise RuntimeError("timed out waiting for bridge device.")
            time.sleep(0.5)


def wait_for_udp_device() -> device:
    d = UdpTransport()
    d.wait_until_ready(timeout=8)
    return d


def get_device() -> device:
    if bridge.is_running():
        return wait_for_bridge_device()

    return wait_for_udp_device()


def is_running() -> bool:
    # When emulator is spawned and killed by user, it has 'defunct' in its process
    check_cmd = "ps -ef | grep 'trezor-emu' | grep -v 'defunct' | grep -v 'grep'"
    process = Popen(check_cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = [part.decode() for part in process.communicate()]
    if stderr:
        log(f"Error when checking emulator process: {stderr}", "red")
    return bool(stdout)


def get_status() -> dict:
    return {"is_running": is_running(), "version": version_running}


def start(version: str, wipe: bool) -> None:
    global proc
    global version_running

    if proc is not None:
        log(
            f"Before starting a new emulator - version {version}, "
            f"killing the already running one - version {version_running}",
            "red",
        )
        stop()

    path = ROOT_DIR / "src/binaries/firmware/bin"

    if version[0] == "2":
        model_t_profile = "/var/tmp/trezor.flash"
        if wipe and os.path.exists(model_t_profile):
            os.remove(model_t_profile)

        command = f"{path}/trezor-emu-core-v{version} -O0 -X heapsize=20M -m main"
    else:
        model_one_profile = ROOT_DIR / "emulator.img"
        if wipe and os.path.exists(model_one_profile):
            os.remove(model_one_profile)

        command = (
            f"TREZOR_OLED_SCALE={TREZOR_ONE_OLED_SCALE} "
            f"{path}/trezor-emu-legacy-v{version} -O0"
        )

    if proc is None:
        # TODO:
        # - check if emulator process is already running and kill it if so
        # - detect if Popen process starts without error (if udp port is listening)
        # - run custom firmware
        # - run T1 emulator
        # - run T1 & T2 emulator at once
        # - run two T2/T1 emulators
        proc = Popen(command, shell=True, preexec_fn=os.setsid)
        log(f"the commandline is {str(proc.args)}")
        version_running = version


def stop() -> None:
    log("Stopping")
    global proc
    global version_running

    if proc is None:
        log("WARNING: Attempting to stop emulator, but it is not running", "red")
    else:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc = None
        version_running = None


def setup_device(
    mnemonic: str,
    pin: str,
    passphrase_protection: bool,
    label: str,
    needs_backup: bool = False,
) -> None:
    # TODO: check if device is acquired, otherwise throws
    #   "wrong previous session" from bridge
    client = TrezorClientDebugLink(get_device())
    client.open()
    time.sleep(SLEEP)
    debuglink.load_device(
        client,
        mnemonic,
        pin,
        passphrase_protection,
        label,
        needs_backup=needs_backup,
    )
    client.close()


def wipe_device() -> None:
    client = TrezorClientDebugLink(get_device())
    client.open()
    time.sleep(SLEEP)
    wipe(client)
    client.close()


def reset_device() -> None:
    client = TrezorClientDebugLink(get_device())
    client.open()
    time.sleep(SLEEP)
    reset(client, skip_backup=True, pin_protection=False)
    client.close()


def press_yes() -> None:
    client = DebugLink(get_device().find_debug())
    client.open()
    time.sleep(SLEEP)
    client.press_yes()
    client.close()


def press_no() -> None:
    client = DebugLink(get_device().find_debug())
    client.open()
    time.sleep(SLEEP)
    client.press_no()
    client.close()


# enter recovery word or pin
# enter pin not possible for T2, it is locked, for T1 it is possible
# change pin possible, use input(word=pin-string)
def input(value: str) -> None:
    client = DebugLink(get_device().find_debug())
    client.open()
    time.sleep(SLEEP)
    client.input(value)
    client.close()


def swipe(direction: str) -> None:
    client = DebugLink(get_device().find_debug())
    client.open()
    time.sleep(SLEEP)
    if direction == "up":
        client.swipe_up()
    elif direction == "right":
        client.swipe_right()
    elif direction == "down":
        client.swipe_down()
    elif direction == "left":
        client.swipe_left()
    client.close()


def read_and_confirm_mnemonic() -> None:
    # Connecting to the device
    client = DebugLink(get_device().find_debug())
    client.open()
    time.sleep(SLEEP)

    # Clicking continue button
    client.press_yes()
    time.sleep(SLEEP)

    # Scrolling through all the 12 words on next three pages
    for _ in range(3):
        client.swipe_up()
        time.sleep(SLEEP)

    # Confirming that I have written the seed down
    client.press_yes()
    time.sleep(SLEEP)

    # Retrieving the seed words for next "quiz"
    mnem = client.state().mnemonic_secret.decode("utf-8")
    mnemonic = mnem.split()
    time.sleep(SLEEP)

    # Answering 3 questions asking for a specific word
    for _ in range(3):
        index = client.read_reset_word_pos()
        client.input(mnemonic[index])
        time.sleep(SLEEP)

    # Click Continue to finish the quiz
    client.press_yes()
    time.sleep(SLEEP)

    # Click Continue to finish the backup
    client.press_yes()
    time.sleep(SLEEP)

    client.close()


def read_and_confirm_shamir_mnemonic(shares: int = 1, threshold: int = 1) -> None:
    """Performs a walkthrough of the whole Shamir backup on the device.

    NOTE: does not support Super Shamir.
    """
    MIN_SHARES = 1
    MAX_SHARES = 16
    if shares < MIN_SHARES or shares > MAX_SHARES:
        raise RuntimeError(
            f"Number of shares must be between {MIN_SHARES} and {MAX_SHARES}."
        )
    if threshold > shares:
        raise RuntimeError("Threshold cannot be bigger than number of shares.")

    # For setting the right amount of shares/thresholds, we need location of buttons
    MINUS_BUTTON_COORDS = (60, 70)
    PLUS_BUTTON_COORDS = (180, 70)

    # Connecting to the device
    client = DebugLink(get_device().find_debug())
    client.open()
    time.sleep(SLEEP)

    # Click Continue to begin Shamir setup process
    client.press_yes()
    time.sleep(SLEEP)

    # Clicking the minus/plus button to set right number of shares (it starts at 5)
    DEFAULT_SHARES = 5
    needed_clicks = abs(shares - DEFAULT_SHARES)
    if needed_clicks > 0:
        if shares < DEFAULT_SHARES:
            button_coords_to_click = MINUS_BUTTON_COORDS
        else:
            button_coords_to_click = PLUS_BUTTON_COORDS

        for _ in range(needed_clicks):
            client.click(button_coords_to_click)
            time.sleep(SLEEP)

    # Click Continue to confirm the number of shares
    client.press_yes()
    time.sleep(SLEEP)

    # Click Continue to set threshold
    client.press_yes()
    time.sleep(SLEEP)

    # When we have 1 or 2 shares, the threshold is set and cannot be changed
    # (it will be 1 and 2 respectively)
    # Otherise assign it correctly by clicking the plus/minus button
    if shares not in [1, 2]:
        # Default threshold can be calculated from the share number
        default_threshold = shares // 2 + 1
        needed_clicks = abs(threshold - default_threshold)
        if needed_clicks > 0:
            if threshold < default_threshold:
                button_coords_to_click = MINUS_BUTTON_COORDS
            else:
                button_coords_to_click = PLUS_BUTTON_COORDS

            for _ in range(needed_clicks):
                client.click(button_coords_to_click)
                time.sleep(SLEEP)

    # Click Continue to confirm our chosen threshold
    client.press_yes()
    time.sleep(SLEEP)

    # Click Continue to continue
    client.press_yes()
    time.sleep(SLEEP)

    # Click I understand
    client.press_yes()
    time.sleep(SLEEP)

    # Loop through all the shares and fulfill all checks
    for _ in range(shares):
        # Scrolling through all the 20 words on next 5 pages
        # While doing so, saving all the words on the screen for the "quiz" later
        mnemonic = []
        for _ in range(5):
            mnemonic.extend(client.read_reset_word().split())
            client.swipe_up()
            time.sleep(SLEEP)

        mnemonic.extend(client.read_reset_word().split())
        assert len(mnemonic) == 20

        # Confirming that I have written the seed down
        client.press_yes()
        time.sleep(SLEEP)

        # Answering 3 questions asking for a specific word
        for _ in range(3):
            index = client.read_reset_word_pos()
            client.input(mnemonic[index])
            time.sleep(SLEEP)

        # Click Continue to finish this quiz
        client.press_yes()
        time.sleep(SLEEP)

    # Click Continue to finish the backup
    client.press_yes()
    time.sleep(SLEEP)

    client.close()


def select_num_of_words(num_of_words: int = 12) -> None:
    client = DebugLink(get_device().find_debug())
    client.open()
    time.sleep(SLEEP)
    client.input(str(num_of_words))
    client.close()


def apply_settings(
    language: Optional[str] = None,
    label: Optional[str] = None,
    use_passphrase: Optional[bool] = None,
    homescreen: Optional[str] = None,
    auto_lock_delay_ms: Optional[int] = None,
    display_rotation: Optional[int] = None,
    passphrase_always_on_device: Optional[bool] = None,
    safety_checks: Optional[int] = None,
) -> None:
    """Forwards settings fields to be applied on a device.

    NOTE: does not handle the experimental_features argument,
      seems that it is not yet supported in latest trezorlib
    """
    # Homescreen needs to be bytes object, so if there,
    #   it should be encoded from the received string
    homescreen_bytes = homescreen.encode() if homescreen else None

    client = TrezorClientDebugLink(get_device())
    client.open()
    time.sleep(SLEEP)
    device.apply_settings(
        client,
        label=label,
        language=language,
        use_passphrase=use_passphrase,
        homescreen=homescreen_bytes,
        passphrase_always_on_device=passphrase_always_on_device,
        auto_lock_delay_ms=auto_lock_delay_ms,
        display_rotation=display_rotation,
        safety_checks=safety_checks,
    )
    client.close()


def allow_unsafe() -> None:
    client = TrezorClientDebugLink(get_device())
    # ignore for Legacy firmware, there is no such setting
    if client.features.major_version == 1:
        return
    client.open()
    time.sleep(SLEEP)
    device.apply_settings(client, safety_checks=1)  # TODO
    client.close()
