from __future__ import annotations

import sys
from pathlib import Path

# Make src/nightly_versions.py importable when running tests from repo root.
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import nightly_versions as nv


def _build_trzf_image(major: int, minor: int, patch: int, codelen: int = 16) -> bytes:
    header = bytearray(1024)
    header[0:4] = b"TRZF"
    header[0x04:0x08] = (1024).to_bytes(4, "little")
    header[0x0C:0x10] = codelen.to_bytes(4, "little")
    header[0x10] = major
    header[0x11] = minor
    header[0x12] = patch
    return bytes(header) + (b"\xaa" * codelen)


def test_version_from_trzf_header_valid() -> None:
    image = _build_trzf_image(2, 13, 7)
    assert nv._version_from_trzf_header(image, 0) == "2.13.7"


def test_version_from_trzf_header_wrong_magic() -> None:
    image = bytearray(_build_trzf_image(2, 13, 7))
    image[0:4] = b"ABCD"
    assert nv._version_from_trzf_header(bytes(image), 0) is None


def test_version_from_trzf_header_truncated() -> None:
    # Less than 1024 bytes cannot contain a valid TRZF header.
    truncated = b"TRZF" + b"\x00" * 100
    assert nv._version_from_trzf_header(truncated, 0) is None


def test_version_from_core_binary_valid() -> None:
    vendor_header_len = 512
    vendor = bytearray(vendor_header_len)
    vendor[0:4] = b"TRZV"
    vendor[0x04:0x08] = vendor_header_len.to_bytes(4, "little")
    blob = b"\x00" * 33 + bytes(vendor) + _build_trzf_image(2, 12, 3)

    assert nv._version_from_core_binary(blob) == "2.12.3"


def test_version_from_core_binary_invalid_layout() -> None:
    # TRZV exists, but hdrlen points past the blob, so parsing must fail.
    vendor = bytearray(64)
    vendor[0:4] = b"TRZV"
    vendor[0x04:0x08] = (10_000).to_bytes(4, "little")
    blob = bytes(vendor) + _build_trzf_image(2, 12, 3)

    assert nv._version_from_core_binary(blob) is None


def test_version_from_legacy_binary_valid() -> None:
    legacy = bytearray(256)
    legacy[0:4] = b"TRZR"
    blob = bytes(legacy) + _build_trzf_image(1, 14, 2)

    assert nv._version_from_legacy_binary(blob) == "1.14.2"


def test_version_from_legacy_binary_wrong_magic() -> None:
    blob = b"XXXX" + (b"\x00" * 252) + _build_trzf_image(1, 14, 2)
    assert nv._version_from_legacy_binary(blob) is None


def test_read_nightly_binary_falls_back_when_direct_unreadable(
    tmp_path, monkeypatch
) -> None:
    prefix = "trezor-emu-core-T2T1-v2-main"
    direct = tmp_path / prefix
    fallback = tmp_path / f"{prefix}-arm"
    direct.write_bytes(b"direct")
    fallback.write_bytes(b"fallback")

    original_read_bytes = Path.read_bytes

    def fake_read_bytes(path: Path) -> bytes:
        if path == direct:
            raise OSError("simulated direct read error")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fake_read_bytes)

    assert nv._read_nightly_binary(tmp_path, prefix) == b"fallback"


def test_read_nightly_binary_continues_after_candidate_error(
    tmp_path, monkeypatch
) -> None:
    prefix = "trezor-emu-core-T3W1-v2-main"
    bad_candidate = tmp_path / f"{prefix}-a"
    good_candidate = tmp_path / f"{prefix}-b"
    bad_candidate.write_bytes(b"bad")
    good_candidate.write_bytes(b"good")

    original_read_bytes = Path.read_bytes

    def fake_read_bytes(path: Path) -> bytes:
        if path == bad_candidate:
            raise OSError("simulated candidate read error")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fake_read_bytes)

    assert nv._read_nightly_binary(tmp_path, prefix) == b"good"
