use std::fs;
use std::path::PathBuf;
use std::process::{Command, Stdio};

use crate::state::AppState;

fn worker_bin_path(state: &AppState) -> Option<PathBuf> {
    let exe = if cfg!(windows) { "worker-server.exe" } else { "worker-server" };
    let p = state.bin.join(exe);
    p.exists().then_some(p)
}

pub fn spawn(state: &AppState) -> Result<String, String> {
    state.ensure_storage();

    let out_log = state.logs.join("worker.out.log");
    let err_log = state.logs.join("worker.err.log");
    let stdout = fs::File::create(&out_log).map_err(|e| e.to_string())?;
    let stderr = fs::File::create(&err_log).map_err(|e| e.to_string())?;

    let mut cmd = if let Some(bin) = worker_bin_path(state) {
        let mut c = Command::new(&bin);
        c.current_dir(&state.reshort);
        c
    } else {
        let python = crate::utils::find_python().ok_or("python not found on PATH")?;
        let root = crate::utils::find_worker_root()
            .ok_or("worker package not found (set REVOICE_WORKER_DIR)")?;
        let mut c = Command::new(&python);
        c.arg("-m").arg("worker.server").current_dir(&root);
        c
    };

    cmd.env("REVOICE_SERVER_URL", &state.server_url);
    if state.bin.exists() {
        let bin = state.bin.to_string_lossy().into_owned();
        cmd.env("FFMPEG_BIN", &bin);
        let sep = if cfg!(target_os = "windows") { ";" } else { ":" };
        let path = std::env::var("PATH").unwrap_or_default();
        cmd.env("PATH", format!("{bin}{sep}{path}"));
    }
    cmd.stdout(Stdio::from(stdout)).stderr(Stdio::from(stderr));
    crate::utils::no_window(&mut cmd);
    let child = cmd.spawn().map_err(|e| e.to_string())?;
    state.replace_worker(child);

    Ok(out_log.to_string_lossy().into_owned())
}

pub fn healthy(state: &AppState) -> bool {
    crate::services::worker_api::healthy(&state.worker_url)
}

pub fn ensure_running(state: &AppState) {
    if !healthy(state) {
        let _ = spawn(state);
    }
}