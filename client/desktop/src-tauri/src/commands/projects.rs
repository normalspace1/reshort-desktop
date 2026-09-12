use serde_json::{json, Value};
use tauri::State;

use crate::services::downloader::{self, VideoInfo};
use crate::services::{storage, worker_api};
use crate::state::AppState;

#[tauri::command]
pub async fn fetch_video_info(state: State<'_, AppState>, url: String) -> Result<VideoInfo, String> {
    let bin = state.bin.clone();
    tauri::async_runtime::spawn_blocking(move || downloader::video_info(&url, &bin))
        .await
        .map_err(|e| format!("task join: {e}"))?
}

#[tauri::command]
pub fn start_generation(
    state: State<AppState>,
    url: String,
    keep_memes: Option<bool>,
    uniquify: Option<bool>,
    adapt_tts: Option<bool>,
    voice_id: Option<String>,
    voice: Option<String>,
    tts_base_speed: Option<f64>,
    burn_subtitles: Option<bool>,
    title: Option<String>,
    author: Option<String>,
    thumbnail: Option<String>,
) -> Result<Value, String> {
    crate::services::worker::ensure_running(&state);

    let keep = keep_memes.unwrap_or(true);
    let uniq = uniquify.unwrap_or(true);
    let adapt = adapt_tts.unwrap_or(true);
    let project_id = crate::utils::short_id(&url);
    storage::ensure_project_record(
        &state,
        &project_id,
        &title.unwrap_or_else(|| "Unknown".into()),
        &author.unwrap_or_else(|| "Unknown".into()),
        &thumbnail.unwrap_or_default(),
        &url,
        keep,
        uniq,
        adapt,
    );

    let projects = state.projects.clone();
    let bin = state.bin.clone();
    let worker_url = state.worker_url.clone();
    let pid = project_id.clone();
    let url_child = url.clone();

    std::thread::spawn(move || {
        if let Err(e) = downloader::download_into_project(&projects, &pid, &url_child, &bin) {
            log::error!("download failed for {url_child}: {e}");
            storage::set_project_error(&projects, &pid, &format!("Ошибка скачивания: {e}"));
            return;
        }
        match downloader::extract_thumbnail(&projects, &pid, &bin) {
            Ok(_) => {
                storage::update_thumbnail(&projects, &pid, &format!("{}/api/thumbnail/{}", worker_url, pid));
            }
            Err(e) => log::warn!("thumbnail extract failed for {pid}: {e}"),
        }
        let mut payload = json!({
            "url": url_child,
            "project_id": pid,
            "keep_memes": keep,
            "uniquify": uniq,
            "adapt_tts": adapt,
            "voice_id": voice_id,
        });
        if let Some(v) = voice {
            payload["voice"] = json!(v);
        }
        if let Some(s) = tts_base_speed {
            payload["tts_base_speed"] = json!(s);
        }
        if let Some(b) = burn_subtitles {
            payload["burn_subtitles"] = json!(b);
        }
        if let Err(e) = worker_api::start_processing(&worker_url, &payload) {
            log::error!("worker generate: {e}");
            storage::set_project_error(&projects, &pid, &format!("Ошибка запуска воркера: {e}"));
        }
    });

    Ok(json!({ "project_id": project_id, "status": "started" }))
}

#[tauri::command]
pub fn get_project_status(state: State<AppState>, project_id: String) -> Value {
    storage::project_status(&state, &project_id)
}

#[tauri::command]
pub fn list_projects(state: State<AppState>) -> Value {
    storage::list_projects(&state)
}

#[tauri::command]
pub fn get_video_url(state: State<AppState>, project_id: String) -> Value {
    if storage::final_video_path(&state, &project_id).exists() {
        json!({ "url": format!("{}/api/video/{}", state.worker_url, project_id), "exists": true })
    } else {
        json!({ "url": Value::Null, "exists": false })
    }
}

#[tauri::command]
pub fn open_project_folder(state: State<AppState>, project_id: String) -> Result<Value, String> {
    if project_id.trim().is_empty()
        || project_id.contains('/')
        || project_id.contains('\\')
        || project_id.contains("..")
    {
        return Err("invalid project id".to_string());
    }
    let dir = state.projects.join(&project_id);
    if !dir.is_dir() {
        return Err("project folder not found".to_string());
    }
    let path = dir.to_string_lossy().into_owned();

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

#[tauri::command]
pub fn delete_project(state: State<AppState>, project_id: String) -> Result<Value, String> {
    if project_id.trim().is_empty()
        || project_id.contains('/')
        || project_id.contains('\\')
        || project_id.contains("..")
    {
        return Err("invalid project id".to_string());
    }
    let dir = state.projects.join(&project_id);
    if dir.exists() {
        std::fs::remove_dir_all(&dir).map_err(|e| format!("delete {dir:?}: {e}"))?;
    }
    Ok(json!({ "ok": true }))
}

#[tauri::command]
pub fn clear_projects(state: State<AppState>, project_id: Option<String>) -> Result<Value, String> {
    let _ = project_id;
    let root = state.projects.clone();
    let mut removed = 0usize;
    let rd = std::fs::read_dir(&root).map_err(|e| format!("read projects root: {e}"))?;
    for entry in rd.flatten() {
        let name = entry.file_name().to_string_lossy().into_owned();
        // Only project-prefixed directories (short_id => rv_<hex>) are ever removed.
        if name.starts_with("rv_") && entry.path().is_dir() {
            std::fs::remove_dir_all(entry.path())
                .map_err(|e| format!("delete {name}: {e}"))?;
            removed += 1;
        }
    }
    Ok(json!({ "ok": true, "removed": removed }))
}

#[tauri::command]
pub async fn pick_video_file() -> Result<Option<String>, String> {
    let file = rfd::AsyncFileDialog::new()
        .add_filter("Видео файлы", &["mp4", "mov", "mkv", "webm", "avi", "m4v"])
        .pick_file()
        .await;
    Ok(file.map(|f| f.path().to_string_lossy().into_owned()))
}

#[tauri::command]
pub async fn pick_video_folder() -> Result<Option<String>, String> {
    let folder = rfd::AsyncFileDialog::new().pick_folder().await;
    Ok(folder.map(|f| f.path().to_string_lossy().into_owned()))
}

#[tauri::command]
pub fn scan_folder_videos(folder: String) -> Result<Vec<String>, String> {
    let path = std::path::Path::new(&folder);
    if !path.is_dir() {
        return Err("Указанный путь не является папкой".into());
    }
    let mut videos = Vec::new();
    let video_exts = ["mp4", "mov", "mkv", "webm", "avi", "m4v"];
    if let Ok(rd) = std::fs::read_dir(path) {
        for entry in rd.flatten() {
            let p = entry.path();
            if p.is_file() {
                if let Some(ext) = p.extension().and_then(|s| s.to_str()) {
                    if video_exts.contains(&ext.to_lowercase().as_str()) {
                        videos.push(p.to_string_lossy().into_owned());
                    }
                }
            }
        }
    }
    videos.sort();
    Ok(videos)
}

#[tauri::command]
pub fn start_local_generation(
    state: State<AppState>,
    file_path: String,
    voice: Option<String>,
    tts_base_speed: Option<f64>,
    burn_subtitles: Option<bool>,
    keep_memes: Option<bool>,
    uniquify: Option<bool>,
    adapt_tts: Option<bool>,
) -> Result<Value, String> {
    let src_path = std::path::PathBuf::from(&file_path);
    if !src_path.is_file() {
        return Err("Файл не найден".into());
    }
    crate::services::worker::ensure_running(&state);

    let keep = keep_memes.unwrap_or(true);
    let uniq = uniquify.unwrap_or(true);
    let adapt = adapt_tts.unwrap_or(true);

    let file_stem = src_path
        .file_stem()
        .map(|s| s.to_string_lossy().into_owned())
        .unwrap_or_else(|| "Local Video".into());

    let nonce = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0);
    let project_id = crate::utils::short_id(&format!("local:{}:{nonce}", src_path.display()));

    storage::ensure_project_record(
        &state,
        &project_id,
        &file_stem,
        "Локальное видео",
        "",
        &file_path,
        keep,
        uniq,
        adapt,
    );

    let projects = state.projects.clone();
    let bin = state.bin.clone();
    let worker_url = state.worker_url.clone();
    let pid = project_id.clone();
    let src_child = src_path.clone();

    std::thread::spawn(move || {
        let input_dir = projects.join(&pid).join("input");
        if let Err(e) = std::fs::create_dir_all(&input_dir) {
            log::error!("create input dir failed: {e}");
            storage::set_project_error(&projects, &pid, &format!("Ошибка создания папки: {e}"));
            return;
        }
        let target_video = input_dir.join("src.f616.mp4");
        if let Err(e) = std::fs::copy(&src_child, &target_video) {
            log::error!("copy local video failed: {e}");
            storage::set_project_error(&projects, &pid, &format!("Ошибка копирования видео: {e}"));
            return;
        }

        match downloader::extract_thumbnail(&projects, &pid, &bin) {
            Ok(_) => {
                storage::update_thumbnail(&projects, &pid, &format!("{}/api/thumbnail/{}", worker_url, pid));
            }
            Err(e) => log::warn!("thumbnail extract failed for local {pid}: {e}"),
        }

        let mut payload = json!({
            "url": format!("file://{}", src_child.display()),
            "project_id": pid,
            "keep_memes": keep,
            "uniquify": uniq,
            "adapt_tts": adapt,
        });
        if let Some(v) = voice {
            payload["voice"] = json!(v);
        }
        if let Some(s) = tts_base_speed {
            payload["tts_base_speed"] = json!(s);
        }
        if let Some(b) = burn_subtitles {
            payload["burn_subtitles"] = json!(b);
        }
        if let Err(e) = worker_api::start_processing(&worker_url, &payload) {
            log::error!("worker generate: {e}");
            storage::set_project_error(&projects, &pid, &format!("Ошибка запуска воркера: {e}"));
        }
    });

    Ok(json!({ "project_id": project_id, "status": "started" }))
}

#[tauri::command]
pub fn start_batch_generation(
    state: State<AppState>,
    file_paths: Vec<String>,
    voice: Option<String>,
    tts_base_speed: Option<f64>,
    burn_subtitles: Option<bool>,
    keep_memes: Option<bool>,
    uniquify: Option<bool>,
    adapt_tts: Option<bool>,
) -> Result<Value, String> {
    let mut started_ids = Vec::new();
    for file_path in file_paths {
        if let Ok(res) = start_local_generation(
            state.clone(),
            file_path,
            voice.clone(),
            tts_base_speed,
            burn_subtitles,
            keep_memes,
            uniquify,
            adapt_tts,
        ) {
            if let Some(id) = res["project_id"].as_str() {
                started_ids.push(id.to_string());
            }
        }
    }
    Ok(json!({ "started_count": started_ids.len(), "project_ids": started_ids }))
}