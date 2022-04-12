import base64
import os
import stat
import sys
import time
import urllib.request
from pathlib import Path
from subprocess import PIPE
from typing import Literal, Optional
from urllib.error import HTTPError

from psutil import Popen
from trezorlib import debuglink, device, messages
from trezorlib._internal.emulator import CoreEmulator, LegacyEmulator
from trezorlib.debuglink import DebugLink, TrezorClientDebugLink
from trezorlib.exceptions import TrezorFailure
from trezorlib.transport.bridge import BridgeTransport
from trezorlib.transport.udp import UdpTransport

import binaries
import bridge
import helpers

# TODO: consider creating a class from this module to avoid these globals
version_running = None
EMULATOR = None

ROOT_DIR = Path(__file__).parent.parent.resolve()
FIRMWARE_DIR = ROOT_DIR / "src/binaries/firmware/bin"

FW_PATH = ROOT_DIR / "src/binaries/firmware/bin"
IDENTIFIER_T1 = "trezor-emu-legacy-v"
IDENTIFIER_TT = "trezor-emu-core-v"

SCREEN_DIR = ROOT_DIR / "logs/screens"
SCREEN_DIR.mkdir(exist_ok=True)

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


def get_url_identifier(url: str) -> str:
    return url.replace("/", "-").replace(":", "-")


def start_from_url(
    url: str,
    model: Literal["1", "2"],
    wipe: bool,
    output_to_logfile: bool = True,
    save_screenshots: bool = False,
) -> None:
    # Creating an identifier of emulator from this URL, so we have to
    # download it only once and can reuse it any time later
    emu_name = f"{model}-url-{get_url_identifier(url)}"

    # Deciding the location to save depending on being T1/TT
    # (to be compatible with already existing emulators)
    if model == "1":
        emu_path = FW_PATH / f"{IDENTIFIER_T1}{emu_name}"
    elif model == "2":
        emu_path = FW_PATH / f"{IDENTIFIER_TT}{emu_name}"
    else:
        raise RuntimeError("Only 1 and 2 are supported Trezor versions")

    # Downloading only if it does not yet exist
    if not emu_path.is_file():
        log(f"Emulator from {url} will be saved under {emu_path}")
        try:
            urllib.request.urlretrieve(url, emu_path)
        except HTTPError as e:
            err = f"HTTP error when downloading emulator from {url}, err: {e}"
            log(err, "red")
            raise RuntimeError(err)
        # We need to run chmod +x on the newly downloaded file
        emu_path.chmod(emu_path.stat().st_mode | stat.S_IEXEC)
    else:
        log(f"Emulator from {url} already exists under {emu_path}")

    return start(emu_name, wipe, output_to_logfile, save_screenshots)


def start(
    version: str,
    wipe: bool,
    output_to_logfile: bool = True,
    save_screenshots: bool = False,
) -> None:
    global version_running
    global EMULATOR

    # When we are on ARM, include appropriate suffix for the version if not there
    if binaries.IS_ARM and not version.endswith(binaries.ARM_IDENTIFIER):
        log("ARM detected, adding suffix to emulator version", "yellow")
        version += binaries.ARM_IDENTIFIER

    if EMULATOR is not None:
        log(
            f"Before starting a new emulator - version {version}, "
            f"killing the already running one - version {version_running}",
            "red",
        )
        stop()

    # Conditionally redirecting the output to a logfile instead of terminal/stdout
    if output_to_logfile:
        logfile = open(helpers.EMU_BRIDGE_LOG, "a")
    else:
        logfile = sys.stdout

    if version[0] == "2":
        EMULATOR = CoreEmulator(
            FIRMWARE_DIR / f"trezor-emu-core-v{version}",
            profile_dir=FIRMWARE_DIR,
            logfile=logfile,
        )
    elif version[0] == "1":
        os.environ["TREZOR_OLED_SCALE"] = str(TREZOR_ONE_OLED_SCALE)
        EMULATOR = LegacyEmulator(
            FIRMWARE_DIR / f"trezor-emu-legacy-v{version}",
            profile_dir=FIRMWARE_DIR,
            logfile=logfile,
        )
    else:
        raise RuntimeError("Version can start only with 1 or 2")

    if wipe and EMULATOR.storage.exists():
        EMULATOR.storage.unlink()

    EMULATOR.start()

    log(f"Emulator spawned. PID: {EMULATOR.process.pid}. CMD: {EMULATOR.process.args}")

    # Verifying if the emulator is really running
    time.sleep(0.5)
    if EMULATOR.process.poll() is not None:
        EMULATOR = None
        raise RuntimeError(f"Emulator version {version} is unable to run!")

    version_running = version

    # Optionally saving the screenshots on any screen-change, so we can send the
    # current screen on demand
    # Only applicable to TT, T1 is not capable of screenshotting
    if save_screenshots and version[0] == "2":
        time.sleep(1)
        client = DebugLink(get_device().find_debug())
        client.open()
        client.start_recording(str(SCREEN_DIR))


def stop() -> None:
    log("Stopping")
    global version_running
    global EMULATOR

    if EMULATOR is None:
        log("WARNING: Attempting to stop emulator, but it is not running", "red")
    else:
        emu_pid = EMULATOR.process.pid
        EMULATOR.stop()
        log(f"Emulator killed. PID: {emu_pid}.")
        EMULATOR = None
        version_running = None


def get_current_screen() -> str:
    """Return the screenshot encoded as base64."""
    # Screenshots are being saved automatically on screen-change,
    # so we take the latest file
    all_screenshots = list(SCREEN_DIR.glob("*.png"))
    if not all_screenshots:
        raise RuntimeError(
            "There are no screenshots. Did you start emulator with save_screenshots=True?"
        )
    latest_screenshot = max(all_screenshots, key=lambda p: p.stat().st_ctime)

    with open(latest_screenshot, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode()
        return encoded_string


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
    device.wipe(client)
    client.close()


def reset_device(
    backup_type: messages.BackupType, strength: int, use_shamir: bool = False
) -> None:
    client = TrezorClientDebugLink(get_device())
    client.open()
    time.sleep(SLEEP)

    if use_shamir:
        backup_type = 1

    device.reset(
        client,
        skip_backup=True,
        pin_protection=False,
        backup_type=backup_type,
        strength=strength,
    )
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


def click(x: int, y: int) -> None:
    client = DebugLink(get_device().find_debug())
    client.open()
    time.sleep(SLEEP)
    client.click((x, y))
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
    experimental_features: Optional[int] = None,
) -> None:
    """Forwards settings fields to be applied on a device."""
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
        experimental_features=experimental_features,
    )
    client.close()


def allow_unsafe() -> None:
    client = TrezorClientDebugLink(get_device())
    client.open()
    time.sleep(SLEEP)

    # T1 does not support PromptAlways
    if client.features.major_version == 1:
        safety_checks = messages.SafetyCheckLevel.PromptTemporarily
    else:
        safety_checks = messages.SafetyCheckLevel.PromptAlways

    # Some older devices do not support safety checks, so we know
    # the command will fail with a specific error message
    # T1 supports safety checks from 1.10.1 and T2 from 2.3.2
    try:
        device.apply_settings(client, safety_checks=safety_checks)
    except TrezorFailure as err:
        # Catching only specific error message, otherwise reraising the exception
        if "No setting provided" in str(err):
            log(
                f"Could not allow unsafe. Device does not support safety checks. Err: {err}",
                "red",
            )
        else:
            raise
    client.close()
