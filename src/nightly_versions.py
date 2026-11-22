from __future__ import annotations

import json
from pathlib import Path


def _metadata_file(bin_dir: Path) -> Path:
    return bin_dir / "nightly-versions.json"


def _read_u32_le(data: bytes, offset: int) -> int | None:
    if offset < 0 or offset + 4 > len(data):
        return None
    return int.from_bytes(data[offset : offset + 4], "little")


def _version_from_trzf_header(data: bytes, offset: int) -> str | None:
    # TRZF firmware header has fixed 1024-byte size and version bytes at 0x10-0x12.
    if offset < 0 or offset + 1024 > len(data):
        return None
    if data[offset : offset + 4] != b"TRZF":
        return None

    hdrlen = _read_u32_le(data, offset + 0x04)
    codelen = _read_u32_le(data, offset + 0x0C)
    if hdrlen != 1024 or codelen is None or codelen <= 0:
        return None

    end_of_image = offset + hdrlen + codelen
    if end_of_image > len(data):
        return None

    major = data[offset + 0x10]
    minor = data[offset + 0x11]
    patch = data[offset + 0x12]
    return f"{major}.{minor}.{patch}"


def _version_from_core_binary(data: bytes) -> str | None:
    # Core firmware image starts with TRZV vendor header followed by TRZF.
    search_from = 0
    while True:
        vendor_offset = data.find(b"TRZV", search_from)
        if vendor_offset == -1:
            return None

        vendor_hdrlen = _read_u32_le(data, vendor_offset + 0x04)
        if vendor_hdrlen is not None and vendor_hdrlen > 0:
            trzf_offset = vendor_offset + vendor_hdrlen
            version = _version_from_trzf_header(data, trzf_offset)
            if version is not None:
                return version

        search_from = vendor_offset + 1


def _version_from_legacy_binary(data: bytes) -> str | None:
    # Legacy images may be TRZR (256-byte header) + TRZF (v2 header).
    search_from = 0
    while True:
        legacy_offset = data.find(b"TRZR", search_from)
        if legacy_offset == -1:
            break

        version = _version_from_trzf_header(data, legacy_offset + 256)
        if version is not None:
            return version

        search_from = legacy_offset + 1

    return None


def _read_nightly_binary(bin_dir: Path, prefix: str) -> bytes | None:
    direct = bin_dir / prefix
    if direct.is_file():
        try:
            return direct.read_bytes()
        except OSError:
            pass

    # ARM nightly names currently append -arm suffix.
    candidates = sorted(bin_dir.glob(f"{prefix}*"))
    for candidate in candidates:
        if candidate.is_file():
            try:
                return candidate.read_bytes()
            except OSError:
                continue

    return None


def write_nightly_versions_metadata(bin_dir: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    nightly_binaries = {
        "T1B1": (
            "trezor-emu-legacy-T1B1-v1-main",
            _version_from_legacy_binary,
        ),
        "T2T1": ("trezor-emu-core-T2T1-v2-main", _version_from_core_binary),
        "T3B1": ("trezor-emu-core-T3B1-v2-main", _version_from_core_binary),
        "T3T1": ("trezor-emu-core-T3T1-v2-main", _version_from_core_binary),
        "T3W1": ("trezor-emu-core-T3W1-v2-main", _version_from_core_binary),
    }

    for name, (prefix, parser) in nightly_binaries.items():
        data = _read_nightly_binary(bin_dir, prefix)
        if data is None:
            continue

        version = parser(data)
        if version is not None:
            parsed[name] = version

    metadata = read_nightly_versions_metadata(bin_dir)
    metadata.update(parsed)

    destination = _metadata_file(bin_dir)
    with destination.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)
        f.write("\n")
    return metadata


def read_nightly_versions_metadata(bin_dir: Path) -> dict[str, str]:
    metadata_path = _metadata_file(bin_dir)
    if not metadata_path.is_file():
        return {}

    try:
        with metadata_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    versions: dict[str, str] = {}
    for key in ("T1B1", "T2T1", "T3B1", "T3T1", "T3W1"):
        value = data.get(key)
        if isinstance(value, str):
            versions[key] = value

    return versions
