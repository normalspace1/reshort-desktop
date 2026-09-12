use serde_json::{json, Value};
use tauri::State;

use crate::services::worker;
use crate::state::AppState;

#[tauri::command]
pub fn spawn_worker(state: State<AppState>) -> Result<Value, String> {
    let log = worker::spawn(&state)?;
    Ok(json!({ "ok": true, "worker_url": state.worker_url, "log": log }))
}

#[tauri::command]
pub fn worker_health(state: State<AppState>) -> Value {
    json!({ "ok": worker::healthy(&state) })
}