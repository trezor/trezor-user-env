import os
import signal
import time
from pathlib import Path
from subprocess import PIPE, Popen

import bridge
from trezorlib import debuglink, device  # type: ignore
from trezorlib.debuglink import DebugLink  # type: ignore
from trezorlib.debuglink import TrezorClientDebugLink
from trezorlib.device import reset, wipe  # type: ignore
from trezorlib.transport.bridge import BridgeTransport  # type: ignore
from trezorlib.transport.udp import UdpTransport  # type: ignore

# TODO: consider creating a class from this module to avoid these globals
proc = None
version_running = None

ROOT_DIR = Path(__file__).parent.parent.resolve()

# when communicating with device via bridge/debuglink, this sleep is required otherwise there
# may appear weird race conditions in communications. when not going through bridge but webusb
# there is no need for it, but we can skip bridge only when doing initial setup before test.
SLEEP = 0.501

# makes Trezor One emulator larger
TREZOR_ONE_OLED_SCALE = 2


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
    ps = Popen(check_cmd, shell=True, stdout=PIPE)
    output = ps.stdout.read().decode()  # type: ignore
    ps.stdout.close()  # type: ignore
    ps.wait()
    return bool(output)


def get_status() -> dict:
    return {"is_running": is_running(), "version": version_running}


def start(version: str, wipe: bool) -> None:
    global proc
    global version_running

    if proc is not None:
        print(
            f"Before starting a new emulator - version {version}, "
            f"killing the already running one - version {version_running}"
        )
        stop()

    path = ROOT_DIR / "firmware/bin"

    if version[0] == "2":
        model_t_profile = "/var/tmp/trezor.flash"
        if wipe and os.path.exists(model_t_profile):
            os.remove(model_t_profile)

        command = f"{path}/trezor-emu-core-v{version} -O0 -X heapsize=20M -m main"
    else:
        model_one_profile = ROOT_DIR / "emulator.img"
        if wipe and os.path.exists(model_one_profile):
            os.remove(model_one_profile)

        command = f"TREZOR_OLED_SCALE={TREZOR_ONE_OLED_SCALE} {path}/trezor-emu-legacy-v{version} -O0"

    if proc is None:
        # TODO:
        # - check if emulator process is already running and kill it if so
        # - detect if Popen process starts without error (if udp port is listening)
        # - run custom firmware
        # - run T1 emulator
        # - run T1 & T2 emulator at once
        # - run two T2/T1 emulators
        proc = Popen(command, shell=True, preexec_fn=os.setsid)
        print(f"the commandline is {str(proc.args)}")
        version_running = version


def stop() -> None:
    global proc
    global version_running

    if proc is not None:
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
    # TODO:
    # - check if device is acquired otherwise throws "wrong previous session" from bridge
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


def select_num_of_words(num_of_words: int = 12) -> None:
    client = DebugLink(get_device().find_debug())
    client.open()
    time.sleep(SLEEP)
    client.input(str(num_of_words))
    client.close()


def apply_settings(passphrase_always_on_device: bool = False) -> None:
    client = TrezorClientDebugLink(get_device())
    client.open()
    time.sleep(SLEEP)
    device.apply_settings(
        client,
        passphrase_always_on_device=passphrase_always_on_device,
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
