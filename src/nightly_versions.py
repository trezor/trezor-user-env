from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path


def _metadata_file(bin_dir: Path) -> Path:
    return bin_dir / "nightly-versions.json"


def _parse_version_h(version_h: str) -> str | None:
    parts: dict[str, str] = {}
    expected = {"VERSION_MAJOR", "VERSION_MINOR", "VERSION_PATCH"}

    for raw_line in version_h.splitlines():
        line = raw_line.strip()
        if not line.startswith("#define "):
            continue
        tokens = line.split()
        if len(tokens) < 3:
            continue

        key = tokens[1]
        value = tokens[2]
        if key in expected and value.isdigit():
            parts[key] = value

    if not expected.issubset(parts.keys()):
        return None

    return f"{parts['VERSION_MAJOR']}.{parts['VERSION_MINOR']}.{parts['VERSION_PATCH']}"


def write_nightly_versions_metadata(bin_dir: Path) -> dict[str, str]:
    fetched: dict[str, str] = {}
    sources = {
        "2-main": "https://raw.githubusercontent.com/trezor/trezor-firmware/main/core/embed/projects/firmware/version.h",
        "1-main": "https://raw.githubusercontent.com/trezor/trezor-firmware/main/legacy/firmware/version.h",
    }

    for name, url in sources.items():
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                content = response.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError):
            continue

        version = _parse_version_h(content)
        if version is not None:
            fetched[name] = version

    metadata = read_nightly_versions_metadata(bin_dir)
    metadata.update(fetched)

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
    for key in ("2-main", "1-main"):
        value = data.get(key)
        if isinstance(value, str):
            versions[key] = value

    return versions
