use std::fs;
use std::path::Path;
use std::time::Duration;

use serde::Serialize;

use crate::utils;

#[derive(Serialize)]
pub struct VideoInfo {
    pub title: String,
    pub author: String,
    pub thumbnail: String,
    pub duration: f64,
}

pub fn video_info(url: &str, bin_dir: &Path) -> Result<VideoInfo, String> {
    let yt = utils::find_ytdlp(bin_dir).ok_or("yt-dlp not found (run setup)")?;
    let out = utils::run_output(
        &yt,
        &["--dump-single-json", "--skip-download", "--no-warnings", "--no-playlist", url],
        None,
        Duration::from_secs(60),
    )?;
    let j: serde_json::Value =
        serde_json::from_str(&out).map_err(|e| format!("yt-dlp JSON parse: {e}"))?;
    Ok(VideoInfo {
        title: j["title"].as_str().unwrap_or("Unknown").to_string(),
        author: j["uploader"]
            .as_str()
            .or(j["channel"].as_str())
            .or(j["extractor"].as_str())
            .unwrap_or("Unknown")
            .to_string(),
        thumbnail: j["thumbnail"].as_str().unwrap_or("").to_string(),
        duration: j["duration"].as_f64().unwrap_or(0.0),
    })
}

pub fn download_into_project(
    projects_root: &Path,
    project_id: &str,
    url: &str,
    bin_dir: &Path,
) -> Result<(), String> {
    let input = projects_root.join(project_id).join("input");
    fs::create_dir_all(&input).map_err(|e| e.to_string())?;
    let out = input.join("src.f616.mp4");
    let _ = fs::remove_file(&out);

    let yt = utils::find_ytdlp(bin_dir).ok_or("yt-dlp not found (run setup)")?;
    let out_arg = out.to_string_lossy().into_owned();
    let base = "bv*[ext=mp4][vcodec^=avc1][height<=1080]";
    let selectors = [
        format!("{base}+ba[ext=m4a]"),
        "bv[ext=mp4]+ba[ext=m4a]".to_string(),
        "b[ext=mp4]/b".to_string(),
        "best".to_string(),
    ];

    for sel in &selectors {
        if utils::run_output(
            &yt,
            &[
                "--no-progress",
                "--no-playlist",
                "--merge-output-format",
                "mp4",
                "-f",
                sel,
                "-o",
                &out_arg,
                url,
            ],
            None,
            Duration::from_secs(600),
        )
        .is_err()
        {
            continue;
        }
        if out.exists() && out.metadata().map(|m| m.len() > 0).unwrap_or(false) {
            return Ok(());
        }
    }
    Err(format!("yt-dlp download failed for {url}"))
}

pub fn extract_thumbnail(
    projects_root: &Path,
    project_id: &str,
    bin_dir: &Path,
) -> Result<std::path::PathBuf, String> {
    let input = projects_root.join(project_id).join("input");
    let video = input.join("src.f616.mp4");
    if !video.exists() {
        return Err("video not downloaded".into());
    }
    let out = input.join("thumb.jpg");
    let ffmpeg = crate::utils::find_ffmpeg(bin_dir).ok_or("ffmpeg not found (run setup)")?;
    crate::utils::run_output(
        &ffmpeg,
        &[
            "-y",
            "-ss", "2",
            "-i", &video.to_string_lossy(),
            "-frames:v", "1",
            "-vf", "scale=320:-2",
            "-q:v", "4",
            &out.to_string_lossy(),
        ],
        None,
        Duration::from_secs(60),
    )
    .map_err(|e| format!("ffmpeg thumbnail: {e}"))?;
    if out.exists() && out.metadata().map(|m| m.len() > 0).unwrap_or(false) {
        Ok(out)
    } else {
        Err("ffmpeg produced no thumbnail".into())
    }
}