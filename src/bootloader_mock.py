"""A minimal mock Trezor device that reports it is in *bootloader mode*.

The real Trezor emulator has no bootloader (see docs: "neither boardloader nor
bootloader and no firmware uploads"), so there is no way to put the emulator
into bootloader mode. Suite / host apps only need the device to *present* as a
bootloader though - i.e. answer `Initialize`/`GetFeatures` with
`Features.bootloader_mode = True` over the wire - to exercise their bootloader
and firmware-update flows.

This module is exactly that: a tiny UDP server that speaks Trezor wire
**protocol v1** (plaintext) on the emulator port. The bootloader always uses
protocol v1 on every model (THP is firmware-only), so a single v1 mock covers
both T2T1 and T3W1. The bridge discovers it over UDP just like a real emulator.

It answers the handful of messages a host sends in bootloader mode
(GetFeatures/Initialize, Ping, Cancel, WipeDevice) and drives a stubbed
firmware-update flow (FirmwareErase -> FirmwareRequest* -> Success) so the whole
Suite update flow can run to completion (as a no-op flash).
"""

from __future__ import annotations

import socket
import struct
import threading
from typing import Optional

from trezorlib import mapping, messages, models

import helpers

log = helpers.log

# Protocol-v1 framing (mirrors trezorlib.protocol_v1 / transport.udp).
HEADER_FMT = ">HL"
HEADER_LEN = struct.calcsize(HEADER_FMT)
CHUNK_SIZE = 64
PING = b"PINGPING"
PONG = b"PONGPONG"

DEFAULT_PORT = 21324
MAPPING = mapping.DEFAULT_MAPPING

# Chunk size the mock "requests" during the v2 firmware-upload flow. Small
# enough to yield several progress steps for a typical firmware image.
FW_REQUEST_CHUNK = 64 * 1024

# Module-global server handle so the controller can start/stop a single mock.
_SERVER: Optional["BootloaderMockServer"] = None


def _build_features(model: str) -> messages.Features:
    """Bootloader-mode Features for the given (internal) model name."""
    trezor_model = models.by_internal_name(model)
    if trezor_model is None:
        raise RuntimeError(f"Unknown model {model}")
    return messages.Features(
        vendor="trezor.io",
        major_version=2,
        minor_version=1,
        patch_version=7,
        bootloader_mode=True,
        device_id=None,
        model=trezor_model.name,
        internal_model=trezor_model.internal_name,
        firmware_present=True,
        fw_major=2,
        fw_minor=9,
        fw_patch=0,
        fw_vendor="trezor.io",
        unlocked=True,
        bootloader_locked=False,
        firmware_corrupted=False,
        capabilities=[],
    )


class BootloaderMockServer:
    def __init__(self, model: str, port: int = DEFAULT_PORT) -> None:
        self.model = model
        self.port = port
        self.features = _build_features(model)
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        # Firmware-update flow state (v2 chunked method).
        self._fw_total = 0
        self._fw_received = 0

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", self.port))
        sock.settimeout(0.2)
        self._sock = sock
        self._stop.clear()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        log(
            f"Bootloader mock ({self.model}) listening on udp:127.0.0.1:{self.port}",
            "blue",
        )

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        if self._sock is not None:
            self._sock.close()
            self._sock = None
        log(f"Bootloader mock ({self.model}) stopped", "blue")

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # -- wire framing ------------------------------------------------------
    def _serve(self) -> None:
        assert self._sock is not None
        while not self._stop.is_set():
            try:
                chunk, addr = self._sock.recvfrom(CHUNK_SIZE)
            except socket.timeout:
                continue
            except OSError:
                break

            if chunk[:8] == PING:
                self._sock.sendto(PONG, addr)
                continue

            msg = self._read_message(chunk, addr)
            if msg is None:
                continue
            try:
                reply = self._dispatch(msg)
            except Exception as e:  # noqa: BLE001 - mock must not crash
                log(f"Bootloader mock error handling {msg.__class__.__name__}: {e!r}", "red")
                reply = messages.Failure(
                    code=messages.FailureType.FirmwareError, message=str(e)
                )
            if reply is not None:
                self._write_message(reply, addr)

    def _read_message(self, first_chunk: bytes, addr) -> Optional[messages.protobuf.MessageType]:
        """Reassemble a protocol-v1 message that started with `first_chunk`."""
        assert self._sock is not None
        if first_chunk[:3] != b"?##":
            return None
        body = first_chunk[3:]
        msg_type, datalen = struct.unpack(HEADER_FMT, body[:HEADER_LEN])
        buffer = bytearray(body[HEADER_LEN:])
        while len(buffer) < datalen:
            try:
                chunk, chunk_addr = self._sock.recvfrom(CHUNK_SIZE)
            except socket.timeout:
                if self._stop.is_set():
                    return None
                continue
            if chunk_addr != addr or chunk[:1] != b"?":
                continue
            buffer.extend(chunk[1:])
        return MAPPING.decode(msg_type, bytes(buffer[:datalen]))

    def _write_message(self, msg: messages.protobuf.MessageType, addr) -> None:
        assert self._sock is not None
        msg_type, data = MAPPING.encode(msg)
        payload = b"##" + struct.pack(HEADER_FMT, msg_type, len(data)) + data
        for i in range(0, len(payload), CHUNK_SIZE - 1):
            chunk = b"?" + payload[i : i + CHUNK_SIZE - 1]
            chunk = chunk.ljust(CHUNK_SIZE, b"\x00")
            self._sock.sendto(chunk, addr)

    # -- message dispatch --------------------------------------------------
    def _dispatch(self, msg: messages.protobuf.MessageType):
        if isinstance(msg, (messages.Initialize, messages.GetFeatures)):
            return self.features
        if isinstance(msg, messages.Ping):
            return messages.Success(message=msg.message or "")
        if isinstance(msg, messages.Cancel):
            return messages.Failure(
                code=messages.FailureType.ActionCancelled, message="Cancelled"
            )
        if isinstance(msg, messages.WipeDevice):
            return messages.Success(message="Device wiped")
        if isinstance(msg, messages.FirmwareErase):
            self._fw_total = msg.length or 0
            self._fw_received = 0
            return self._next_firmware_request()
        if isinstance(msg, messages.FirmwareUpload):
            self._fw_received += len(msg.payload or b"")
            return self._next_firmware_request()
        if isinstance(msg, messages.GetFirmwareHash):
            return messages.FirmwareHash(hash=b"\x00" * 32)
        return messages.Failure(
            code=messages.FailureType.UnexpectedMessage,
            message=f"Bootloader mock: unhandled {msg.__class__.__name__}",
        )

    def _next_firmware_request(self):
        """Drive the v2 chunked upload; Success once the whole image is in."""
        if self._fw_received >= self._fw_total:
            return messages.Success(message="Firmware installed")
        length = min(FW_REQUEST_CHUNK, self._fw_total - self._fw_received)
        return messages.FirmwareRequest(offset=self._fw_received, length=length)


# -- module-level API mirroring emulator/tropic_model ----------------------
def start(model: str, port: int = DEFAULT_PORT) -> None:
    global _SERVER
    if _SERVER is not None and _SERVER.is_running():
        _SERVER.stop()
    _SERVER = BootloaderMockServer(model=model, port=port)
    _SERVER.start()


def stop() -> None:
    global _SERVER
    if _SERVER is not None:
        _SERVER.stop()
        _SERVER = None


def is_running() -> bool:
    return _SERVER is not None and _SERVER.is_running()


def get_status() -> dict:
    if _SERVER is not None and _SERVER.is_running():
        return {"is_running": True, "model": _SERVER.model}
    return {"is_running": False, "model": None}


if __name__ == "__main__":
    import argparse
    import time

    parser = argparse.ArgumentParser(description="Trezor bootloader-mode mock device")
    parser.add_argument("--model", default="T3W1", help="internal model name, e.g. T2T1 / T3W1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    start(args.model, args.port)
    print(f"Bootloader mock ({args.model}) on udp:127.0.0.1:{args.port} - Ctrl-C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop()
