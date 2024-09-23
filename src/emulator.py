from __future__ import annotations

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
from typing import Any, Dict, Generator, Optional, TypedDict
from urllib.error import HTTPError

from psutil import Popen
from trezorlib import debuglink, device, messages, models
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
VERSION_RUNNING: str | None = None
EMULATOR: CoreEmulator | LegacyEmulator | None = None

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
    if helpers.physical_trezor():
        return {"is_running": True, "version": "PHYSICAL_TREZOR"}
    else:
        return {"is_running": is_running(), "version": VERSION_RUNNING}


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
    if binaries.IS_ARM and not emu_name.endswith(binaries.ARM_IDENTIFIER):
        emu_name = f"{emu_name}{binaries.ARM_IDENTIFIER}"

    # Deciding the location to save depending on being T1/TT/TR
    # (to be compatible with already existing emulators)
    model_identifier = binaries.MODEL_IDENTIFIERS.get(model)
    if not model_identifier:
        raise RuntimeError(f"Unknown model {model}")
    emu_path = binaries.USER_DOWNLOADED_DIR / f"{model_identifier}{emu_name}"

    # Downloading only if it does not yet exist
    if not emu_path.is_file():
        log(f"Emulator from {url} will be saved under {emu_path}")
        try:
            urllib.request.urlretrieve(url, emu_path)
        except HTTPError as first_err:
            if binaries.IS_ARM and not url.endswith(binaries.ARM_IDENTIFIER):
                log(
                    "ARM detected, trying to download the ARM version of the emulator",
                    "yellow",
                )
                url = f"{url}{binaries.ARM_IDENTIFIER}"
                log(f"Trying to download ARM from {url}")
                try:
                    urllib.request.urlretrieve(url, emu_path)
                except HTTPError as e:
                    err = f"HTTP error when downloading emulator from {url}, err: {e}"
                    log(err, "red")
                    raise RuntimeError(err)
            else:
                err = (
                    f"HTTP error when downloading emulator from {url}, err: {first_err}"
                )
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
    global VERSION_RUNNING
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
            f"killing the already running one - {VERSION_RUNNING}",
            "red",
        )
        stop()

    # Conditionally redirecting the output to a logfile instead of terminal/stdout
    if output_to_logfile:
        logfile = open(helpers.EMU_BRIDGE_LOG, "a")
    else:
        logfile = sys.stdout

    emu_location = Path(binaries.get_firmware_location(model, version))

    if model in ("T2T1", "T2B1", "T3T1"):
        EMULATOR = CoreEmulator(
            emu_location,
            profile_dir=binaries.FIRMWARE_BIN_DIR,
            logfile=logfile,
        )
    elif model == "T1B1":
        os.environ["TREZOR_OLED_SCALE"] = str(TREZOR_ONE_OLED_SCALE)
        EMULATOR = LegacyEmulator(
            emu_location,
            profile_dir=str(binaries.FIRMWARE_BIN_DIR),
            logfile=logfile,
        )
    else:
        raise RuntimeError(f"Unknown model {model}")

    assert EMULATOR is not None

    if wipe and EMULATOR.storage.exists():
        EMULATOR.storage.unlink()

    try:
        EMULATOR.start()
    except Exception:
        # When emulators fails to start, setting it to empty state not to cause issues later
        EMULATOR = None
        raise

    log(f"Emulator spawned. PID: {EMULATOR.process.pid}. CMD: {EMULATOR.process.args}")  # type: ignore

    # Verifying if the emulator is really running
    time.sleep(0.5)
    assert EMULATOR.process is not None
    if EMULATOR.process.poll() is not None:
        EMULATOR = None
        raise RuntimeError(f"Emulator version {version} is unable to run!")

    VERSION_RUNNING = version_model()

    # Optionally saving the screenshots on any screen-change, so we can send the
    # current screen on demand
    # Creating a new directory for each emulator session, so the screens are not being overwritten
    # NOT supported for T1, as it needs Debuglink for screenshot creation, and therefore
    # it would not save screenshots for example from Suite and other interaction.
    if save_screenshots and model != "T1B1":
        time.sleep(SLEEP)
        with connect_to_debuglink() as debug:
            # Need to set model info (both TT and TR are under same category)
            debug.model = models.T2T1
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
    global VERSION_RUNNING
    global EMULATOR

    if EMULATOR is None:
        log("WARNING: Attempting to stop emulator, but it is not running", "red")
    else:
        assert EMULATOR.process is not None
        emu_pid = EMULATOR.process.pid
        EMULATOR.stop()
        log(f"Emulator killed. PID: {emu_pid}.")
        EMULATOR = None
        VERSION_RUNNING = None


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
        else:
            raise ValueError(f"Unknown direction: {direction}")


def assert_text_on_screen(debug: DebugLink, text: str) -> None:
    layout = debug.read_layout()
    real_text = layout.text_content()
    assert text.lower() in real_text.lower(), f"Expected text: {text}, got: {real_text}"


def assert_seed_words(debug: DebugLink, amount: int) -> None:
    layout = debug.read_layout()
    seed_words = layout.seed_words()
    real_amount = len(seed_words)
    assert real_amount == amount, f"Expected seed words: {amount}, got: {real_amount}"


def read_and_confirm_mnemonic() -> None:
    with connect_to_client() as client:
        internal_model = client.features.internal_model

    if internal_model == models.T2T1.internal_name:
        read_and_confirm_mnemonic_t2t1()
    else:
        raise RuntimeError(f"Model {internal_model} not supported for this operation.")


def read_and_confirm_mnemonic_t2t1() -> None:
    with connect_to_debuglink() as debug:
        debug.watch_layout(True)

        preview_texts = [
            "backup contains 12 words",
            "anywhere digital",
        ]
        for expected_text in preview_texts:
            assert_text_on_screen(debug, expected_text)
            debug.press_yes()
            time.sleep(SLEEP)

        # Two swipes and confirm of the seed words
        assert_seed_words(debug, 4)
        debug.swipe_up()
        time.sleep(SLEEP)

        assert_seed_words(debug, 4)
        debug.swipe_up()
        time.sleep(SLEEP)

        assert_seed_words(debug, 4)
        debug.press_yes()
        time.sleep(SLEEP)

        # Retrieving the seed words for next "quiz"
        secret_bytes = debug.state().mnemonic_secret
        assert secret_bytes is not None
        mnem = secret_bytes.decode("utf-8")
        mnemonic = mnem.split()
        assert (
            len(mnemonic) == 12
        ), f"Expected 12 words in mnemonic, got {len(mnemonic)}"
        time.sleep(SLEEP)

        # Answering 3 questions asking for a specific word
        for _ in range(3):
            layout = debug.read_layout()
            screen_text = layout.text_content()
            # "Select word 3 of 20"
            #              ^
            assert_text_on_screen(debug, "select word")
            word_pos = int(screen_text.split()[2])
            wanted_word = mnemonic[word_pos - 1].lower()
            debug.input(wanted_word)
            time.sleep(SLEEP)

        # Click Continue to finish the quiz
        assert_text_on_screen(debug, "finished verifying")
        debug.press_yes()
        time.sleep(SLEEP)

        # Click Continue to finish the backup
        assert_text_on_screen(debug, "backup is done")
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
    OK_BUTTON_COORDS = (200, 200)

    with connect_to_debuglink() as debug:
        # So that we can wait layout
        debug.watch_layout(True)

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
        debug.click(OK_BUTTON_COORDS)
        time.sleep(SLEEP)

        # Click Continue to set threshold
        debug.press_yes()
        time.sleep(SLEEP)

        # When we have 1 or 2 shares, the threshold is set and cannot be changed
        # (it will be 1 and 2 respectively)
        # Otherwise assign it correctly by clicking the plus/minus button
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
            mnemonic: list[str] = []
            layout = debug.read_layout()
            for _ in range(layout.page_count() - 1):
                mnemonic.extend(layout.seed_words())
                layout = debug.swipe_up(wait=True)  # type: ignore
                assert layout is not None
            mnemonic.extend(layout.seed_words())

            assert len(mnemonic) == 20

            # Confirming that I have written the seed down
            debug.press_yes()
            time.sleep(SLEEP)

            # Answering 3 questions asking for a specific word
            for _ in range(3):
                layout = debug.wait_layout()
                # "Select word 3 of 20"
                #              ^
                word_pos = int(layout.text_content().split()[2])
                wanted_word = mnemonic[word_pos - 1].lower()
                debug.input(wanted_word)
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
        debug_state_dict: Dict[str, Any] = {}
        for key in dir(debug_state):
            val = getattr(debug_state, key)
            # Not interested in private attributes and non-JSON fields (bytes)
            if key.startswith("__") or key[0].isupper():
                continue
            if isinstance(val, bytes):
                try:
                    val = val.decode("utf-8")
                except UnicodeDecodeError:
                    val = val.hex()

            debug_state_dict[key] = val

        return debug_state_dict


class ScreenContent(TypedDict):
    title: str
    body: str


def get_screen_content() -> ScreenContent:
    with connect_to_debuglink(needs_udp=True) as debug:
        layout = debug.read_layout()
        title = layout.title()
        body = layout.text_content()
        return {"title": title, "body": body}


# For testing/debugging purposes
if __name__ == "__main__":
    read_and_confirm_mnemonic()
