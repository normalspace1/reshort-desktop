use std::fs;
use std::path::{Path, PathBuf};

use serde_json::{json, Value};

use crate::state::AppState;

pub fn project_status(state: &AppState, project_id: &str) -> Value {
    let path = state.projects.join(project_id).join("project.json");
    fs::read_to_string(&path)
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_else(|| json!({ "id": project_id, "status": "queued" }))
}

pub fn list_projects(state: &AppState) -> Value {
    let mut out: Vec<Value> = Vec::new();
    if let Ok(rd) = fs::read_dir(&state.projects) {
        for entry in rd.flatten() {
            let id = entry.file_name().to_string_lossy().into_owned();
            let pj = entry.path().join("project.json");
            let mut obj = match fs::read_to_string(&pj) {
                Ok(s) => serde_json::from_str(&s).unwrap_or_else(|_| json!({ "id": id.clone() })),
                Err(_) => json!({ "id": id.clone() }),
            };
            obj["has_video"] = json!(final_video_path(state, &id).exists());
            out.push(obj);
        }
    }
    out.sort_by(|a, b| {
        b["created_at"]
            .as_str()
            .unwrap_or("")
            .cmp(a["created_at"].as_str().unwrap_or(""))
    });
    json!(out)
}

pub fn final_video_path(state: &AppState, project_id: &str) -> PathBuf {
    state
        .projects
        .join(project_id)
        .join("output")
        .join("final_video.mp4")
}

pub fn ensure_project_record(
    state: &AppState,
    project_id: &str,
    title: &str,
    author: &str,
    thumbnail: &str,
    url: &str,
    keep_memes: bool,
    uniquify: bool,
    adapt_tts: bool,
) {
    let dir = state.projects.join(project_id);
    let pj = dir.join("project.json");
    if pj.exists() {
        if let Ok(s) = fs::read_to_string(&pj) {
            if let Ok(mut data) = serde_json::from_str::<Value>(&s) {
                data["options"]["url"] = json!(url);
                data["options"]["keep_memes"] = json!(keep_memes);
                data["options"]["uniquify"] = json!(uniquify);
                data["options"]["adapt_tts"] = json!(adapt_tts);
                let _ = fs::write(&pj, serde_json::to_string_pretty(&data).unwrap());
            }
        }
        return;
    }
    if let Err(e) = fs::create_dir_all(&dir) {
        log::warn!("cannot create {}: {}", dir.display(), e);
        return;
    }
    let record = json!({
        "id": project_id,
        "status": "queued",
        "options": {
            "url": url,
            "keep_memes": keep_memes,
            "uniquify": uniquify,
            "adapt_tts": adapt_tts,
        },
        "info": { "title": title, "author": author, "thumbnail": thumbnail },
    });
    if let Err(e) = fs::write(&pj, serde_json::to_string_pretty(&record).unwrap()) {
        log::warn!("cannot write {}: {}", pj.display(), e);
    }
}

pub fn update_thumbnail(projects_root: &Path, project_id: &str, url: &str) {
    let pj = projects_root.join(project_id).join("project.json");
    if let Ok(s) = fs::read_to_string(&pj) {
        if let Ok(mut data) = serde_json::from_str::<Value>(&s) {
            data["info"]["thumbnail"] = json!(url);
            if let Err(e) = fs::write(&pj, serde_json::to_string_pretty(&data).unwrap()) {
                log::warn!("cannot write {}: {}", pj.display(), e);
            }
        }
    }
}

pub fn set_project_error(projects_root: &Path, project_id: &str, error: &str) {
    let pj = projects_root.join(project_id).join("project.json");
    if let Ok(s) = fs::read_to_string(&pj) {
        if let Ok(mut data) = serde_json::from_str::<Value>(&s) {
            data["status"] = json!("failed");
            data["error"] = json!(error);
            if let Err(e) = fs::write(&pj, serde_json::to_string_pretty(&data).unwrap()) {
                log::warn!("cannot write {}: {}", pj.display(), e);
            }
        }
    }
}