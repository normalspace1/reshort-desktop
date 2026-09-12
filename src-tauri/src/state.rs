use std::fs;
use std::path::PathBuf;
use std::process::Child;
use std::sync::Mutex;

use crate::utils;

pub struct AppState {
    pub reshort: PathBuf,
    pub projects: PathBuf,
    pub models: PathBuf,
    pub bin: PathBuf,
    pub logs: PathBuf,
    pub worker_url: String,
    pub server_url: String,
    pub(crate) worker: Mutex<Option<Child>>,
}

impl AppState {
    pub fn new() -> Self {
        let appdata = utils::appdata_dir();
        let reshort = env_path("REVOICE_ROOT", appdata.join("Reshort"));
        let cfg = crate::config::get();
        AppState {
            projects: env_path("REVOICE_PROJECTS_ROOT", reshort.join("projects")),
            models: env_path("REVOICE_MODELS_ROOT", reshort.join("models")),
            bin: env_path("REVOICE_BIN_ROOT", reshort.join("bin")),
            logs: env_path("REVOICE_LOGS_ROOT", reshort.join("logs")),
            worker_url: env_str("REVOICE_WORKER_URL", cfg.worker_url.as_str()),
            server_url: env_str("REVOICE_SERVER_URL", cfg.server_url.as_str()),
            reshort,
            worker: Mutex::new(None),
        }
    }

    pub fn ensure_storage(&self) {
        for dir in [&self.reshort, &self.projects, &self.models, &self.bin, &self.logs] {
            if let Err(e) = fs::create_dir_all(dir) {
                log::warn!("cannot create {}: {}", dir.display(), e);
            }
        }
    }

    pub fn replace_worker(&self, child: Child) {
        if let Some(mut old) = self.worker.lock().unwrap().replace(child) {
            utils::kill_process(&mut old);
        }
    }
}

impl Drop for AppState {
    fn drop(&mut self) {
        if let Some(mut child) = self.worker.lock().unwrap().take() {
            utils::kill_process(&mut child);
        }
    }
}

fn env_path(key: &str, fallback: PathBuf) -> PathBuf {
    std::env::var(key).map(PathBuf::from).unwrap_or(fallback)
}

fn env_str(key: &str, fallback: &str) -> String {
    std::env::var(key).unwrap_or_else(|_| fallback.to_string())
}