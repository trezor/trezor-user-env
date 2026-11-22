#!/usr/bin/env python3
import argparse
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

# When executed directly, python only adds this nested bin/ directory to
# sys.path, so prepend the src/ root to import nightly_versions.py shared helper
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from nightly_versions import write_nightly_versions_metadata

BASE_EMU_URL = "https://data.trezor.io/dev/firmware/releases/emulators-new"
NIGHTLY_BASE_URL = "https://data.trezor.io/dev/firmware/emu-nightly"
DEFAULT_RELEASES_JSON_URL = (
    "https://raw.githubusercontent.com/trezor/trezor-firmware/main/common/releases.json"
)
SUPPORTED_MODELS = ["T1B1", "T2T1", "T3B1", "T3T1", "T3W1"]

# supports one pinned release per model in addition to the 6 latest releases
PINNED_RELEASES: dict[str, str] = {"T2T1": "2.5.3"}


def get_arch_config() -> tuple[str, list[tuple[str, str]]]:
    system_arch = platform.machine().lower()

    if system_arch.startswith("x86_64") or system_arch == "amd64":
        return "", [
            ("trezor-emu-legacy-T1B1-universal", "trezor-emu-legacy-T1B1-v1-main"),
            ("trezor-emu-core-T2T1-universal", "trezor-emu-core-T2T1-v2-main"),
            ("trezor-emu-core-T3B1-universal", "trezor-emu-core-T3B1-v2-main"),
            ("trezor-emu-core-T3T1-universal", "trezor-emu-core-T3T1-v2-main"),
            ("trezor-emu-core-T3W1-universal", "trezor-emu-core-T3W1-v2-main"),
        ]

    if system_arch.startswith("aarch64") or system_arch == "arm64":
        return "-arm", [
            (
                "trezor-emu-arm-legacy-T1B1-universal",
                "trezor-emu-legacy-T1B1-v1-main-arm",
            ),
            (
                "trezor-emu-arm-core-T2T1-universal",
                "trezor-emu-core-T2T1-v2-main-arm",
            ),
            (
                "trezor-emu-arm-core-T3B1-universal",
                "trezor-emu-core-T3B1-v2-main-arm",
            ),
            (
                "trezor-emu-arm-core-T3T1-universal",
                "trezor-emu-core-T3T1-v2-main-arm",
            ),
            (
                "trezor-emu-arm-core-T3W1-universal",
                "trezor-emu-core-T3W1-v2-main-arm",
            ),
        ]

    raise RuntimeError(f"Not a supported arch - {system_arch}")


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def build_release_paths(
    releases_json: dict, suffix: str, minor_limit: int
) -> list[str]:
    firmware_releases = releases_json.get("firmware", {})
    patches_per_series: dict[tuple[str, int, int], list[int]] = {}

    for version, models in firmware_releases.items():
        try:
            major, minor, patch = (int(part) for part in version.split("."))
        except ValueError:
            continue

        for model in models:
            if model not in SUPPORTED_MODELS:
                continue
            key = (model, major, minor)
            patches_per_series.setdefault(key, []).append(patch)

    download_paths = []
    for model in SUPPORTED_MODELS:
        family = "legacy" if model == "T1B1" else "core"
        model_paths: list[str] = []
        pinned_version = PINNED_RELEASES.get(model)
        pinned_version_available = bool(
            pinned_version and model in firmware_releases.get(pinned_version, [])
        )
        if pinned_version_available:
            model_paths.append(
                f"{model}/trezor-emu-{family}-{model}-v{pinned_version}{suffix}"
            )

        # Determine the newest minor series for this model.
        model_series = [
            (major, minor)
            for (series_model, major, minor) in patches_per_series
            if series_model == model
        ]
        newest_series = max(model_series) if model_series else None

        # For the newest series include the two latest patches,
        # for older series only the latest patch.
        series_versions: list[tuple[int, int, int]] = []
        for (series_model, major, minor), patches in patches_per_series.items():
            if series_model != model:
                continue
            sorted_patches = sorted(patches, reverse=True)
            if (major, minor) == newest_series:
                for p in sorted_patches[:2]:
                    series_versions.append((major, minor, p))
            else:
                series_versions.append((major, minor, sorted_patches[0]))

        series_versions.sort(reverse=True)

        selected_count = 0
        for major, minor, patch in series_versions:
            version = f"{major}.{minor}.{patch}"
            if version == pinned_version:
                continue
            model_paths.append(
                f"{model}/trezor-emu-{family}-{model}-v{version}{suffix}"
            )
            selected_count += 1
            if selected_count >= minor_limit:
                break

        download_paths.extend(model_paths)

    return download_paths


def download_file(url: str, destination: Path, required: bool) -> bool:
    try:
        with (
            urllib.request.urlopen(url, timeout=60) as response,
            destination.open("wb") as out,
        ):
            shutil.copyfileobj(response, out)
        return True
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if required:
            raise RuntimeError(
                f"Failed to download required file from {url}: {exc}"
            ) from exc
        print(f"Skipping unavailable release artifact {url}: {exc}")
        return False


def download_releases(
    bin_dir: Path, suffix: str, releases_json_url: str, minor_limit: int
) -> None:
    releases_json = fetch_json(releases_json_url)
    for file_path in build_release_paths(releases_json, suffix, minor_limit):
        output_name = Path(file_path).name
        destination = bin_dir / output_name
        if destination.exists():
            print(f"{output_name} already exists. skipping...")
            continue
        download_file(f"{BASE_EMU_URL}/{file_path}", destination, required=False)


def download_nightly(bin_dir: Path, nightly_files: list[tuple[str, str]]) -> None:
    with tempfile.TemporaryDirectory(dir=bin_dir) as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        for source_name, destination_name in nightly_files:
            source_url = f"{NIGHTLY_BASE_URL}/{source_name}"
            downloaded_path = tmp_dir_path / source_name
            download_file(source_url, downloaded_path, required=True)
            shutil.move(downloaded_path, bin_dir / destination_name)

    write_nightly_versions_metadata(bin_dir)


def postprocess(bin_dir: Path) -> None:
    emulators = sorted(bin_dir.glob("trezor-emu-*"))
    if emulators:
        for emulator in emulators:
            emulator.chmod(emulator.stat().st_mode | stat.S_IXUSR)

        strip_binary = shutil.which("strip")
        if strip_binary:
            subprocess.run(
                [strip_binary, *[str(path) for path in emulators]], check=True
            )

    shutil.rmtree(bin_dir / "macos", ignore_errors=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Trezor firmware emulators")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["all", "releases", "nightly"],
        default="all",
        help="Which set of emulators to download",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    suffix, nightly_files = get_arch_config()
    bin_dir = Path(__file__).resolve().parent

    releases_json_url = os.environ.get("RELEASES_JSON_URL", DEFAULT_RELEASES_JSON_URL)
    minor_limit = int(os.environ.get("RELEASE_MINOR_LIMIT", "6"))

    if args.mode in ("all", "releases"):
        download_releases(bin_dir, suffix, releases_json_url, minor_limit)

    if args.mode in ("all", "nightly"):
        download_nightly(bin_dir, nightly_files)

    postprocess(bin_dir)


if __name__ == "__main__":
    main()
