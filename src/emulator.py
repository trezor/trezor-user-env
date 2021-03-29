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
    client = DebugLink(get_device().find_debug())
    client.open()
    time.sleep(SLEEP)

    client.press_yes()
    time.sleep(SLEEP)

    mnem = client.state().mnemonic_secret.decode("utf-8")
    mnemonic = mnem.split()
    time.sleep(SLEEP)

    client.swipe_up()
    time.sleep(SLEEP)

    client.swipe_up()
    time.sleep(SLEEP)

    client.swipe_up()
    time.sleep(SLEEP)

    client.press_yes()
    time.sleep(SLEEP)

    index = client.read_reset_word_pos()
    client.input(mnemonic[index])
    time.sleep(SLEEP)

    index = client.read_reset_word_pos()
    client.input(mnemonic[index])
    time.sleep(SLEEP)

    index = client.read_reset_word_pos()
    client.input(mnemonic[index])
    time.sleep(SLEEP)

    client.press_yes()
    client.press_yes()
    client.close()


def read_and_confirm_mnemonic_shamir():
    client = DebugLink(get_device().find_debug())
    client.open()
    time.sleep(SLEEP)

    client.press_yes()

    # one group

    client.swipe_left()
    time.sleep(SLEEP)

    client.swipe_left()
    time.sleep(SLEEP)

    client.swipe_left()
    time.sleep(SLEEP)

    client.swipe_left()
    time.sleep(SLEEP)

    client.press_yes()
    time.sleep(SLEEP)

    # one share

    client.press_yes()
    time.sleep(SLEEP)

    # set the treshold for one

    client.press_yes()
    time.sleep(SLEEP)
    client.press_yes()
    time.sleep(SLEEP)
    client.press_yes()
    time.sleep(SLEEP)

    client.press_yes()
    time.sleep(SLEEP)

    mnem = client.state().mnemonic_secret.decode("utf-8")
    mnemonic = mnem.split()
    time.sleep(SLEEP)

    client.swipe_up()
    time.sleep(SLEEP)

    client.swipe_up()
    time.sleep(SLEEP)

    client.swipe_up()
    time.sleep(SLEEP)

    client.swipe_up()
    time.sleep(SLEEP)

    client.swipe_up()
    time.sleep(SLEEP)

    client.press_yes()
    time.sleep(SLEEP)

    index = client.read_reset_word_pos()
    client.input(mnemonic[index])
    time.sleep(SLEEP)

    index = client.read_reset_word_pos()
    client.input(mnemonic[index])
    time.sleep(SLEEP)

    index = client.read_reset_word_pos()
    client.input(mnemonic[index])
    time.sleep(SLEEP)

    client.press_yes()
    client.press_yes()
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
