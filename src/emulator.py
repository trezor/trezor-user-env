import base64
import os
import stat
import sys
import time
import urllib.request
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from subprocess import PIPE
from typing import Any, Dict, Generator, Optional
from urllib.error import HTTPError

from psutil import Popen
from trezorlib import debuglink, device, messages
from trezorlib._internal.emulator import CoreEmulator, LegacyEmulator
from trezorlib.debuglink import DebugLink, TrezorClientDebugLink
from trezorlib.exceptions import TrezorFailure
from trezorlib.transport import Transport
from trezorlib.transport.bridge import BridgeTransport
from trezorlib.transport.udp import UdpTransport

import binaries
import bridge
import helpers

# TODO: consider creating a class from this module to avoid these globals
version_running = None
EMULATOR = None

ROOT_DIR = Path(__file__).resolve().parent.parent

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


def get_bridge_device() -> Transport:
    devices = BridgeTransport.enumerate()
    for d in devices:
        d.find_debug()
        return d
    raise RuntimeError("No debuggable bridge device found")


def wait_for_bridge_device() -> Transport:
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


def wait_for_udp_device() -> Transport:
    d = UdpTransport()
    d.wait_until_ready(timeout=8)
    return d


def get_device() -> Transport:
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


def get_status() -> dict[str, Any]:
    return {"is_running": is_running(), "version": version_running}


def get_url_identifier(url: str) -> str:
    return url.replace("/", "-").replace(":", "-")


def start_from_url(
    url: str,
    model: binaries.Model,
    wipe: bool,
    output_to_logfile: bool = True,
    save_screenshots: bool = False,
) -> None:
    binaries.check_model(model)

    # Creating an identifier of emulator from this URL, so we have to
    # download it only once and can reuse it any time later
    emu_name = f"{model}-url-{get_url_identifier(url)}"

    # Deciding the location to save depending on being T1/TT/TR
    # (to be compatible with already existing emulators)
    if model == "1":
        emu_path = binaries.USER_DOWNLOADED_DIR / f"{binaries.IDENTIFIER_T1}{emu_name}"
    elif model == "2":
        emu_path = binaries.USER_DOWNLOADED_DIR / f"{binaries.IDENTIFIER_TT}{emu_name}"
    elif model == "R":
        emu_path = binaries.USER_DOWNLOADED_DIR / f"{binaries.IDENTIFIER_TR}{emu_name}"

    # Downloading only if it does not yet exist
    if not emu_path.is_file():
        log(f"Emulator from {url} will be saved under {emu_path}")
        try:
            urllib.request.urlretrieve(url, emu_path)
        except HTTPError as e:
            err = f"HTTP error when downloading emulator from {url}, err: {e}"
            log(err, "red")
            raise RuntimeError(err)
        # Running chmod +x on the newly downloaded emulator and
        # patching it so it can run in Nix
        # (patching fail will not cause any python error,
        # so there will be no problems even for machines without Nix)
        emu_path.chmod(emu_path.stat().st_mode | stat.S_IEXEC)
        binaries.patch_emulators_for_nix(str(binaries.USER_DOWNLOADED_DIR))
        # Registering the new emulator so we know its locations
        binaries.register_new_firmware(model, emu_name, str(emu_path))
    else:
        log(f"Emulator from {url} already exists under {emu_path}")

    return start(
        version=emu_name,
        model=model,
        wipe=wipe,
        output_to_logfile=output_to_logfile,
        save_screenshots=save_screenshots,
    )


def start(
    version: str,
    model: binaries.Model,
    wipe: bool,
    output_to_logfile: bool = True,
    save_screenshots: bool = False,
) -> None:
    global version_running
    global EMULATOR

    binaries.check_model(model)

    def version_model() -> str:
        return f"{version} ({model})"

    # When we are on ARM, include appropriate suffix for the version if not there
    if binaries.IS_ARM and not version.endswith(binaries.ARM_IDENTIFIER):
        log("ARM detected, adding suffix to emulator version", "yellow")
        version += binaries.ARM_IDENTIFIER

    if EMULATOR is not None:
        log(
            f"Before starting a new emulator - {version_model()}, "
            f"killing the already running one - {version_running}",
            "red",
        )
        stop()

    # Conditionally redirecting the output to a logfile instead of terminal/stdout
    if output_to_logfile:
        logfile = open(helpers.EMU_BRIDGE_LOG, "a")
    else:
        logfile = sys.stdout

    emu_location = Path(binaries.get_firmware_location(model, version))

    if model in ("2", "R"):
        EMULATOR = CoreEmulator(
            emu_location,
            profile_dir=binaries.FIRMWARE_BIN_DIR,
            logfile=logfile,
            disable_animation=False,
        )
    elif model == "1":
        os.environ["TREZOR_OLED_SCALE"] = str(TREZOR_ONE_OLED_SCALE)
        EMULATOR = LegacyEmulator(
            emu_location,
            profile_dir=str(binaries.FIRMWARE_BIN_DIR),
            logfile=logfile,
        )

    assert EMULATOR is not None

    if wipe and EMULATOR.storage.exists():
        EMULATOR.storage.unlink()

    try:
        EMULATOR.start()
    except Exception:
        # When emulators fails to start, setting it to empty state not to cause issues later
        EMULATOR = None
        raise

    log(f"Emulator spawned. PID: {EMULATOR.process.pid}. CMD: {EMULATOR.process.args}")

    # Verifying if the emulator is really running
    time.sleep(0.5)
    if EMULATOR.process.poll() is not None:
        EMULATOR = None
        raise RuntimeError(f"Emulator version {version} is unable to run!")

    version_running = version_model()

    # Optionally saving the screenshots on any screen-change, so we can send the
    # current screen on demand
    # Creating a new directory for each emulator session, so the screens are not being overwritten
    # NOT supported for T1, as it needs Debuglink for screenshot creation, and therefore
    # it would not save screenshots for example from Suite and other interaction.
    if save_screenshots and model != "1":
        time.sleep(SLEEP)
        with connect_to_debuglink() as debug:
            # Need to set model info (both TT and TR are under same category)
            debug.model = "T"
            dir_to_save = get_new_screenshot_dir()
            log(f"Saving screenshots to {dir_to_save}")
            debug.start_recording(str(dir_to_save))


def get_new_screenshot_dir() -> Path:
    """Creates and returns a new directory to save screenshots in, according to current date"""
    dir_to_save = SCREEN_DIR / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dir_to_save.mkdir(parents=True, exist_ok=True)
    return dir_to_save


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
    all_screenshots = list(SCREEN_DIR.rglob("*.png"))
    if not all_screenshots:
        raise RuntimeError(
            "There are no screenshots. Did you start emulator with save_screenshots=True?"
        )
    latest_screenshot = max(all_screenshots, key=lambda p: p.stat().st_ctime)

    with open(latest_screenshot, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode()
        return encoded_string


@contextmanager
def connect_to_client(
    needs_udp: bool = False,
) -> Generator[TrezorClientDebugLink, None, None]:
    """Connect to the emulator and yield a client instance.
    Disconnect after the action is done.
    """
    # Some functionalities might need UDP, not to mess with bridge
    if needs_udp:
        client = TrezorClientDebugLink(wait_for_udp_device())
    else:
        client = TrezorClientDebugLink(get_device())

    client.open()
    time.sleep(SLEEP)

    try:
        yield client
    finally:
        client.close()


@contextmanager
def connect_to_debuglink(
    needs_udp: bool = False,
) -> Generator[DebugLink, None, None]:
    """Connect to the emulator and yield a debuglink instance.
    Disconnect after the action is done.
    """
    # Some functionalities might need UDP, not to mess with bridge
    if needs_udp:
        client = DebugLink(wait_for_udp_device().find_debug())
    else:
        client = DebugLink(get_device().find_debug())

    client.open()
    time.sleep(SLEEP)

    try:
        yield client
    finally:
        client.close()


def setup_device(
    mnemonic: str,
    pin: str,
    passphrase_protection: bool,
    label: str,
    needs_backup: bool = False,
) -> None:
    # TODO: check if device is acquired, otherwise throws
    #   "wrong previous session" from bridge
    with connect_to_client() as client:
        debuglink.load_device(
            client,
            mnemonic,
            pin,
            passphrase_protection,
            label,
            needs_backup=needs_backup,
        )


def wipe_device() -> None:
    with connect_to_client() as client:
        device.wipe(client)


def reset_device(
    backup_type: messages.BackupType, strength: int, use_shamir: bool = False
) -> None:
    if use_shamir:
        backup_type = messages.BackupType(1)

    with connect_to_client() as client:
        device.reset(
            client,
            skip_backup=True,
            pin_protection=False,
            backup_type=backup_type,
            strength=strength,
        )


def press_yes() -> None:
    with connect_to_debuglink() as debug:
        debug.press_yes()


def press_no() -> None:
    with connect_to_debuglink() as debug:
        debug.press_no()


# enter recovery word or pin
# enter pin not possible for T2, it is locked, for T1 it is possible
# change pin possible, use input(word=pin-string)
def input(value: str) -> None:
    with connect_to_debuglink() as debug:
        debug.input(value)


def click(x: int, y: int) -> None:
    with connect_to_debuglink() as debug:
        debug.click((x, y))


def swipe(direction: str) -> None:
    with connect_to_debuglink() as debug:
        if direction == "up":
            debug.swipe_up()
        elif direction == "right":
            debug.swipe_right()
        elif direction == "down":
            debug.swipe_down()
        elif direction == "left":
            debug.swipe_left()


def read_and_confirm_mnemonic() -> None:
    with connect_to_debuglink() as debug:
        # Clicking continue button
        debug.press_yes()
        time.sleep(SLEEP)

        # Scrolling through all the 12 words on next three pages
        for _ in range(3):
            debug.swipe_up()
            time.sleep(SLEEP)

        # Confirming that I have written the seed down
        debug.press_yes()
        time.sleep(SLEEP)

        # Retrieving the seed words for next "quiz"
        mnem = debug.state().mnemonic_secret.decode("utf-8")
        mnemonic = mnem.split()
        time.sleep(SLEEP)

        # Answering 3 questions asking for a specific word
        for _ in range(3):
            index = debug.read_reset_word_pos()
            debug.input(mnemonic[index])
            time.sleep(SLEEP)

        # Click Continue to finish the quiz
        debug.press_yes()
        time.sleep(SLEEP)

        # Click Continue to finish the backup
        debug.press_yes()
        time.sleep(SLEEP)


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

    with connect_to_debuglink() as debug:
        # Click Continue to begin Shamir setup process
        debug.press_yes()
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
                debug.click(button_coords_to_click)
                time.sleep(SLEEP)

        # Click Continue to confirm the number of shares
        debug.press_yes()
        time.sleep(SLEEP)

        # Click Continue to set threshold
        debug.press_yes()
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
                    debug.click(button_coords_to_click)
                    time.sleep(SLEEP)

        # Click Continue to confirm our chosen threshold
        debug.press_yes()
        time.sleep(SLEEP)

        # Click Continue to continue
        debug.press_yes()
        time.sleep(SLEEP)

        # Click I understand
        debug.press_yes()
        time.sleep(SLEEP)

        # Loop through all the shares and fulfill all checks
        for _ in range(shares):
            # Scrolling through all the 20 words on next 5 pages
            # While doing so, saving all the words on the screen for the "quiz" later
            mnemonic = []
            for _ in range(5):
                mnemonic.extend(debug.read_reset_word().split())
                debug.swipe_up()
                time.sleep(SLEEP)

            mnemonic.extend(debug.read_reset_word().split())
            assert len(mnemonic) == 20

            # Confirming that I have written the seed down
            debug.press_yes()
            time.sleep(SLEEP)

            # Answering 3 questions asking for a specific word
            for _ in range(3):
                index = debug.read_reset_word_pos()
                debug.input(mnemonic[index])
                time.sleep(SLEEP)

            # Click Continue to finish this quiz
            debug.press_yes()
            time.sleep(SLEEP)

        # Click Continue to finish the backup
        debug.press_yes()
        time.sleep(SLEEP)


def select_num_of_words(num_of_words: int = 12) -> None:
    with connect_to_debuglink() as debug:
        debug.input(str(num_of_words))


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

    with connect_to_client() as client:
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


def allow_unsafe() -> None:
    with connect_to_client() as client:
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


def get_debug_state() -> Dict[str, Any]:
    # We need to connect on UDP not to interrupt any bridge sessions
    with connect_to_debuglink(needs_udp=True) as debug:
        debug_state = debug.state()
        debug_state_dict = {}
        for key in dir(debug_state):
            val = getattr(debug_state, key)
            # Not interested in private attributes and non-JSON fields (bytes)
            if key.startswith("__") or key[0].isupper():
                continue
            if val is not None and not isinstance(val, (list, str, bool, int)):
                continue

            debug_state_dict[key] = val

        return debug_state_dict
