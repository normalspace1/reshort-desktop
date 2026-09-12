use std::sync::atomic::{AtomicBool, Ordering};

use serde_json::Value;
use tauri::{Manager, State};

use crate::services::setup::{self, SetupEnv, SetupSnapshot};
use crate::services::worker;
use crate::state::AppState;

static SETUP_STARTED: AtomicBool = AtomicBool::new(false);

pub(crate) fn env_of(state: &AppState) -> SetupEnv {
    SetupEnv {
        bin: state.bin.clone(),
        models: state.models.clone(),
        worker_url: state.worker_url.clone(),
    }
}

pub fn auto_setup(env: &SetupEnv) -> bool {
    if !setup::missing_downloadables(env) {
        return false;
    }
    setup::install(env, None).is_ok()
}

#[tauri::command]
pub fn preflight_check(state: State<AppState>) -> Value {
    setup::check(&env_of(&state))
}

#[tauri::command]
pub fn preflight_progress() -> SetupSnapshot {
    setup::snapshot()
}

#[tauri::command]
pub async fn setup_start(app: tauri::AppHandle) {
    if SETUP_STARTED.swap(true, Ordering::SeqCst) {
        return;
    }
    let env = app.state::<AppState>();
    let env = env_of(&env);
    let handle = app.clone();
    tauri::async_runtime::spawn_blocking(move || {
        let _ = auto_setup(&env);
        if crate::utils::find_ffmpeg(&env.bin).is_some() {
            let h2 = handle.clone();
            let _ = handle.run_on_main_thread(move || {
                let s = h2.state::<AppState>();
                worker::ensure_running(&s);
            });
        }
    });
}

#[tauri::command]
pub async fn preflight_retry(state: State<'_, AppState>) -> Result<Value, String> {
    let env = env_of(&state);
    tauri::async_runtime::spawn_blocking(move || auto_setup(&env))
        .await
        .map_err(|e| format!("task join: {e}"))?;

    if crate::utils::find_ffmpeg(&state.bin).is_some() {
        worker::ensure_running(&state);
    }

    Ok(setup::check(&env_of(&state)))
}