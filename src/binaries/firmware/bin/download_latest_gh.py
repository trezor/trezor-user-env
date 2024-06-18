import os
import shutil
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import requests

OWNER = "trezor"
REPO = "trezor-firmware"
GH_TOKEN = os.environ.get("GH_TOKEN")

if not GH_TOKEN:
    raise ValueError("GH_TOKEN is not set")

# WORKFLOW_ID = ".github/workflows/core.yml"
WORKFLOW_ID = 75504717
BRANCH = "main"
CORE_NAMES = [
    "core-emu-T2T1-universal-debuglink-noasan",
    "core-emu-T2B1-universal-debuglink-noasan",
    "core-emu-T3T1-universal-debuglink-noasan",
]

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GH_TOKEN}",
}

# https://api.github.com/repos/trezor/trezor-firmware/actions/workflows
# https://api.github.com/repos/trezor/trezor-firmware/actions/workflows/75504717
# https://api.github.com/repos/trezor/trezor-firmware/actions/workflows/75504717?event=schedule"
# https://api.github.com/repos/trezor/trezor-firmware/actions/runs/8514990723/artifacts
# https://api.github.com/repos/trezor/trezor-firmware/actions/artifacts/1375804284/zip


def get_all_workflows():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows"
    return requests.get(url, headers=HEADERS).json()


def get_latest_run_id(workflow_id: int, branch: str) -> int | None:
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/{workflow_id}/runs?event=schedule"
    print("url", url)
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    runs = data.get("workflow_runs", [])
    for run in runs:
        # TODO: might also check run["conclusion"] == "success", but it seems to always fail
        if run["head_branch"] == branch and run["status"] == "completed":
            return run["id"]  # type: ignore
    return None


def download_artifacts(run_id: int, job_names: list[str]) -> None:
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs/{run_id}/artifacts"
    print("url", url)
    response = requests.get(url, headers=HEADERS).json()
    artifacts = response.get("artifacts", [])
    for artifact in artifacts:
        name = artifact["name"]
        if job_names and name not in job_names:
            continue

        # core-emu-T2T1-universal-debuglink-noasan
        model_name = name.split("-")[2]
        model_ident = {
            "T2T1": "",
            "T2B1": "-R",
            "T3T1": "-T3T1",
        }[model_name]
        emu_name = f"trezor-emu-core{model_ident}-v2-main"
        print("Downloading", emu_name)

        download_url = artifact["archive_download_url"]
        print("download_url", download_url)
        artifact_response = requests.get(download_url, headers=HEADERS)

        with TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "archive.zip"
            with open(zip_path, "wb") as file:
                file.write(artifact_response.content)
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            source_file_path = Path(temp_dir) / Path("unix/trezor-emu-core")
            shutil.copy(source_file_path, Path.cwd() / emu_name)


if __name__ == "__main__":
    # workflows = get_all_workflows()
    # print("workflows", workflows)

    run_id = get_latest_run_id(WORKFLOW_ID, BRANCH)
    print("run_id", run_id)
    if run_id:
        download_artifacts(run_id, CORE_NAMES)
    else:
        print("No successful runs found on the main branch.")
