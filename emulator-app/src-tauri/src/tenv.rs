//! Launch trezor-user-env (`run.sh -r`) from the repo this app was built in.

use std::fs::File;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;

use tauri::{AppHandle, Emitter};

static RUNNING: AtomicBool = AtomicBool::new(false);

fn repo_dir() -> PathBuf {
    let dir = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    dir.canonicalize().unwrap_or(dir)
}

/// Starts `run.sh -r` in a login shell (Finder-launched apps lack the user's PATH, so `docker`
/// would not be found). Returns the log file path.
#[tauri::command]
pub fn start_tenv(app: AppHandle) -> Result<String, String> {
    if RUNNING.swap(true, Ordering::SeqCst) {
        return Err("trezor-user-env is already starting".into());
    }
    let result = spawn(app);
    if result.is_err() {
        RUNNING.store(false, Ordering::SeqCst);
    }
    result
}

fn spawn(app: AppHandle) -> Result<String, String> {
    let dir = repo_dir();
    if !dir.join("run.sh").is_file() {
        return Err(format!("run.sh not found in {}", dir.display()));
    }
    let log_path = std::env::temp_dir().join("trezor-user-env.log");
    let log = File::create(&log_path).map_err(|e| e.to_string())?;
    let log_err = log.try_clone().map_err(|e| e.to_string())?;
    let shell = std::env::var("SHELL").unwrap_or_else(|_| "/bin/zsh".into());

    let mut child = Command::new(shell)
        .args(["-l", "-c", "exec ./run.sh -r"])
        .current_dir(&dir)
        .stdin(Stdio::null())
        .stdout(log)
        .stderr(log_err)
        .spawn()
        .map_err(|e| format!("Failed to run run.sh: {e}"))?;

    thread::spawn(move || {
        let code = child.wait().ok().and_then(|s| s.code());
        RUNNING.store(false, Ordering::SeqCst);
        let _ = app.emit("tenv-exited", code);
    });

    Ok(log_path.display().to_string())
}
