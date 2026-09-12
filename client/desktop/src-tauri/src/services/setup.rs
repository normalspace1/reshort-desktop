use std::fs;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::sync::{Mutex, OnceLock};
use std::time::{Duration, Instant};

use serde::Serialize;
use serde_json::{json, Value};

use crate::utils;

pub struct SetupEnv {
    pub bin: PathBuf,
    pub models: PathBuf,
    pub worker_url: String,
}

#[derive(Clone, Serialize)]
pub struct SetupProgress {
    pub item: String,
    pub status: String,
    pub done: Option<u64>,
    pub total: Option<u64>,
}

#[derive(Clone, Serialize, Default)]
pub struct SetupSnapshot {
    pub running: bool,
    pub item: String,
    pub status: String,
    pub done: u64,
    pub total: Option<u64>,
}

pub type ProgressCb = Box<dyn Fn(SetupProgress) + Send + Sync>;

static SNAP: OnceLock<Mutex<SetupSnapshot>> = OnceLock::new();

pub fn snapshot() -> SetupSnapshot {
    snap().lock().unwrap().clone()
}

fn snap() -> &'static Mutex<SetupSnapshot> {
    SNAP.get_or_init(|| Mutex::new(SetupSnapshot::default()))
}

fn mark(item: &str, status: &str, done: u64, total: Option<u64>, cb: Option<&ProgressCb>) {
    if let Some(cb) = cb {
        cb(SetupProgress {
            item: item.to_string(),
            status: status.to_string(),
            done: Some(done),
            total,
        });
    }
    *snap().lock().unwrap() = SetupSnapshot {
        running: true,
        item: item.to_string(),
        status: status.to_string(),
        done,
        total,
    };
}

fn check_item(id: &str, ok: bool, detail: String) -> Value {
    json!({ "id": id, "ok": ok, "detail": detail })
}

pub fn check(env: &SetupEnv) -> Value {
    let mut out = Vec::new();

    let ffmpeg = utils::has_local_tool(&env.bin, "ffmpeg");
    out.push(check_item(
        "ffmpeg",
        ffmpeg,
        if ffmpeg { utils::find_ffmpeg(&env.bin).unwrap_or_default() } else { "error_ffmpeg".into() },
    ));

    let ffprobe = utils::has_local_tool(&env.bin, "ffprobe");
    out.push(check_item(
        "ffprobe",
        ffprobe,
        if ffprobe { utils::find_ffprobe(&env.bin).unwrap_or_default() } else { "error_ffprobe".into() },
    ));

    let ytdlp = utils::has_local_tool(&env.bin, "yt-dlp");
    out.push(check_item(
        "ytdlp",
        ytdlp,
        if ytdlp { utils::find_ytdlp(&env.bin).unwrap_or_default() } else { "error_ytdlp".into() },
    ));

    let model = env.models.join("Kim_Vocal_2.onnx");
    let model_ok = model.metadata().map(|m| m.len() > 0).unwrap_or(false);
    out.push(check_item(
        "models",
        model_ok,
        if model_ok {
            model.to_string_lossy().into_owned()
        } else {
            "error_models".into()
        },
    ));

    let worker_ok = crate::services::worker_api::healthy(&env.worker_url);
    out.push(check_item(
        "worker",
        worker_ok,
        if worker_ok { env.worker_url.clone() } else { "error_worker".into() },
    ));

    json!(out)
}

pub fn missing_downloadables(env: &SetupEnv) -> bool {
    check(env)
        .as_array()
        .map(|a| {
            a.iter().any(|it| {
                matches!(
                    it.get("id").and_then(|v| v.as_str()),
                    Some("ffmpeg" | "ffprobe" | "ytdlp" | "models")
                ) && it.get("ok").and_then(|v| v.as_bool()) == Some(false)
            })
        })
        .unwrap_or(false)
}

pub fn install(env: &SetupEnv, on_progress: Option<ProgressCb>) -> Result<Value, String> {
    fs::create_dir_all(&env.bin).map_err(|e| e.to_string())?;
    fs::create_dir_all(&env.models).map_err(|e| e.to_string())?;

    let p: Option<&ProgressCb> = on_progress.as_ref();
    *snap().lock().unwrap() = SetupSnapshot { running: true, ..Default::default() };

    let result = (|| -> Result<Value, String> {
        if !utils::has_local_tool(&env.bin, "ffmpeg") || !utils::has_local_tool(&env.bin, "ffprobe")
        {
            let tell = move |status: &str, done: u64, total: Option<u64>| {
                mark("ffmpeg", status, done, total, p);
            };
            tell("installing", 0, None);
            install_ffmpeg(&env.bin, &crate::config::get().ffmpeg_url, &tell)?;
        }

        if !utils::has_local_tool(&env.bin, "yt-dlp") {
            let tell = move |status: &str, done: u64, total: Option<u64>| {
                mark("ytdlp", status, done, total, p);
            };
            tell("installing", 0, None);
            download_to(
                &crate::config::get().ytdlp_url,
                &env.bin.join(exe_name("yt-dlp")),
                Duration::from_secs(600),
                Some(&tell),
            )?;
        }

        let model = env.models.join("Kim_Vocal_2.onnx");
        if !model.exists() {
            let tell = move |status: &str, done: u64, total: Option<u64>| {
                mark("models", status, done, total, p);
            };
            tell("installing", 0, None);
            download_to(
                &crate::config::get().model_url,
                &model,
                Duration::from_secs(900),
                Some(&tell),
            )?;
        }

        Ok(check(env))
    })();

    snap().lock().unwrap().running = false;
    result
}

fn download_to<F: Fn(&str, u64, Option<u64>)>(
    url: &str,
    dest: &Path,
    timeout: Duration,
    on_progress: Option<&F>,
) -> Result<(), String> {
    let mut tmp = dest.to_path_buf();
    tmp.set_extension("part");
    let _ = fs::remove_file(&tmp);

    let result = (|| -> Result<(), String> {
        let resp = ureq::AgentBuilder::new()
            .timeout(timeout)
            .build()
            .get(url)
            .call()
            .map_err(|e| format!("GET {url}: {e}"))?;
        let total: Option<u64> = resp.header("Content-Length").and_then(|v| v.parse().ok());
        let mut reader = resp.into_reader();
        let mut file = fs::File::create(&tmp).map_err(|e| e.to_string())?;
        let mut buf = [0u8; 256 * 1024];
        let mut done: u64 = 0;
        let mut last_send = Instant::now() - Duration::from_secs(1);
        loop {
            let n = reader.read(&mut buf).map_err(|e| e.to_string())?;
            if n == 0 {
                break;
            }
            file.write_all(&buf[..n]).map_err(|e| e.to_string())?;
            done += n as u64;
            if let Some(cb) = on_progress {
                if last_send.elapsed() >= Duration::from_millis(200) || done == total.unwrap_or(0) {
                    cb("downloading", done, total);
                    last_send = Instant::now();
                }
            }
        }
        Ok(())
    })();

    match result {
        Ok(()) => fs::rename(&tmp, dest).map_err(|e| format!("rename: {e}")),
        Err(e) => {
            let _ = fs::remove_file(&tmp);
            Err(e)
        }
    }
}

fn find_recursive(dir: &Path, name: &str) -> Option<PathBuf> {
    let entries = fs::read_dir(dir).ok()?;
    for entry in entries.flatten() {
        let p = entry.path();
        if p.is_dir() {
            if let Some(found) = find_recursive(&p, name) {
                return Some(found);
            }
        } else if p.file_name().is_some_and(|n| n == name) {
            return Some(p);
        }
    }
    None
}

fn extract_zip(zip: &Path, out: &Path) -> Result<(), String> {
    fs::create_dir_all(out).map_err(|e| e.to_string())?;
    let zip_str = zip.to_string_lossy();
    let out_str = out.to_string_lossy();

    #[cfg(target_os = "windows")]
    {
        let script = format!("Expand-Archive -LiteralPath '{zip_str}' -DestinationPath '{out_str}'");
        let mut cmd = std::process::Command::new("powershell");
        cmd.args(["-NoProfile", "-Command", &script]);
        crate::utils::no_window(&mut cmd);
        let r = cmd.status().map_err(|e| format!("powershell: {e}"))?;
        if r.success() {
            return Ok(());
        }
    }
    utils::run_output(
        "tar",
        &["-xf", &zip_str, "-C", &out_str],
        None,
        Duration::from_secs(300),
    )
    .map(|_| ())
}

fn install_ffmpeg<F: Fn(&str, u64, Option<u64>)>(
    bin: &Path,
    url: &str,
    on_progress: &F,
) -> Result<(), String> {
    let zip = bin.join("ffmpeg-release-essentials.zip");
    download_to(url, &zip, Duration::from_secs(900), Some(on_progress))?;

    on_progress("extracting", 0, None);

    let extract_dir = bin.join("_ffmpeg_extract");
    if extract_dir.exists() {
        fs::remove_dir_all(&extract_dir).map_err(|e| e.to_string())?;
    }
    extract_zip(&zip, &extract_dir)?;

    let ffmpeg = find_recursive(&extract_dir, &exe_name("ffmpeg"))
        .ok_or("ffmpeg.exe not found in archive")?;
    let ffprobe = find_recursive(&extract_dir, &exe_name("ffprobe"))
        .ok_or("ffprobe.exe not found in archive")?;

    fs::copy(&ffmpeg, bin.join(exe_name("ffmpeg"))).map_err(|e| e.to_string())?;
    fs::copy(&ffprobe, bin.join(exe_name("ffprobe"))).map_err(|e| e.to_string())?;

    let _ = fs::remove_file(&zip);
    let _ = fs::remove_dir_all(&extract_dir);
    Ok(())
}

fn exe_name(name: &str) -> String {
    if cfg!(windows) { format!("{name}.exe") } else { name.to_string() }
}