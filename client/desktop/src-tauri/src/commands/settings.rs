use serde_json::{json, Value};
use tauri::State;

use crate::state::AppState;

#[tauri::command]
pub fn storage_paths(state: State<AppState>) -> Value {
    json!({
        "reshort": state.reshort.to_string_lossy(),
        "projects": state.projects.to_string_lossy(),
        "models": state.models.to_string_lossy(),
        "bin": state.bin.to_string_lossy(),
        "logs": state.logs.to_string_lossy(),
        "worker_url": state.worker_url,
        "server_url": state.server_url,
    })
}

#[tauri::command]
pub fn open_path(path: String) -> Result<Value, String> {
    let p = std::path::Path::new(&path);
    if !p.exists() {
        return Err("path does not exist".into());
    }
    #[cfg(target_os = "windows")]
    {
        let mut cmd = std::process::Command::new("explorer");
        cmd.arg(&path);
        crate::utils::no_window(&mut cmd);
        cmd.spawn().map_err(|e| format!("explorer: {e}"))?;
    }
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg(&path)
            .spawn()
            .map_err(|e| format!("open: {e}"))?;
    }
    #[cfg(target_os = "linux")]
    {
        std::process::Command::new("xdg-open")
            .arg(&path)
            .spawn()
            .map_err(|e| format!("xdg-open: {e}"))?;
    }
    Ok(json!({ "ok": true }))
}