use std::io::Read;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::time::{Duration, Instant};

pub fn appdata_dir() -> PathBuf {
    if let Ok(a) = std::env::var("APPDATA") {
        return PathBuf::from(a);
    }
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".into());
    if cfg!(target_os = "macos") {
        PathBuf::from(home).join("Library/Application Support")
    } else {
        PathBuf::from(home).join(".config")
    }
}

#[cfg(target_os = "windows")]
pub fn no_window(cmd: &mut Command) {
    use std::os::windows::process::CommandExt;
    cmd.creation_flags(0x08000000); // CREATE_NO_WINDOW
}

#[cfg(not(target_os = "windows"))]
pub fn no_window(_cmd: &mut Command) {}

pub fn find_python() -> Option<String> {
    for cand in ["python", "py", "python3"] {
        let mut cmd = Command::new(cand);
        cmd.arg("--version");
        no_window(&mut cmd);
        if cmd.output().is_ok_and(|o| o.status.success()) {
            return Some(cand.to_string());
        }
    }
    None
}

pub fn find_ytdlp(bin_dir: &Path) -> Option<String> {
    if let Ok(p) = std::env::var("REVOICE_YTDLP") {
        let b = PathBuf::from(p);
        if b.exists() {
            return Some(b.to_string_lossy().into_owned());
        }
    }
    if let Some(local) = local_tool(bin_dir, "yt-dlp") {
        return Some(local);
    }
    let mut cmd = Command::new("yt-dlp");
    cmd.arg("--version");
    no_window(&mut cmd);
    cmd.output()
        .is_ok_and(|o| o.status.success())
        .then(|| "yt-dlp".to_string())
}

pub fn find_ffmpeg(bin_dir: &Path) -> Option<String> {
    find_tool("ffmpeg", bin_dir)
}

pub fn find_ffprobe(bin_dir: &Path) -> Option<String> {
    find_tool("ffprobe", bin_dir)
}

fn find_tool(name: &str, bin_dir: &Path) -> Option<String> {
    if let Ok(d) = std::env::var("FFMPEG_BIN") {
        if let Some(p) = local_tool(Path::new(&d), name) {
            return Some(p);
        }
    }
    if let Some(local) = local_tool(bin_dir, name) {
        return Some(local);
    }
    let mut cmd = Command::new(name);
    cmd.arg("-version");
    no_window(&mut cmd);
    cmd.output()
        .is_ok_and(|o| o.status.success())
        .then(|| name.to_string())
}

pub fn has_local_tool(bin_dir: &Path, name: &str) -> bool {
    local_tool(bin_dir, name).is_some()
}

fn local_tool(bin_dir: &Path, name: &str) -> Option<String> {
    let exe = if cfg!(windows) { format!("{name}.exe") } else { name.to_string() };
    let p = bin_dir.join(exe);
    p.metadata()
        .map(|m| m.len() > 0)
        .unwrap_or(false)
        .then(|| p.to_string_lossy().into_owned())
}

pub fn find_worker_root() -> Option<PathBuf> {
    if let Ok(p) = std::env::var("REVOICE_WORKER_DIR") {
        let d = PathBuf::from(p);
        if d.join("worker").join("main.py").exists() {
            return Some(d);
        }
    }
    let mut cur = std::env::current_dir().ok();
    for _ in 0..6 {
        if let Some(c) = cur {
            if c.join("worker").join("main.py").exists() {
                return Some(c);
            }
            cur = c.parent().map(Path::to_path_buf);
        }
    }
    None
}

pub fn kill_process(child: &mut Child) {
    #[cfg(target_os = "windows")]
    {
        let pid = child.id();
        let mut cmd = Command::new("taskkill");
        cmd.args(["/PID", &pid.to_string(), "/T", "/F"]);
        no_window(&mut cmd);
        let _ = cmd.status();
    }
    let _ = child.kill();
    let _ = child.wait();
}

pub fn run_output(
    program: &str,
    args: &[&str],
    cwd: Option<&Path>,
    timeout: Duration,
) -> Result<String, String> {
    let mut cmd = Command::new(program);
    cmd.args(args);
    if let Some(c) = cwd {
        cmd.current_dir(c);
    }
    no_window(&mut cmd);
    let mut child = cmd
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("{program}: {e}"))?;

    let mut stdout = child.stdout.take().expect("stdout must be piped");
    let mut stderr = child.stderr.take().expect("stderr must be piped");
    let reader = std::thread::spawn(move || {
        let mut out = Vec::new();
        let mut err = Vec::new();
        let _ = stdout.read_to_end(&mut out);
        let _ = stderr.read_to_end(&mut err);
        (out, err)
    });

    let deadline = Instant::now() + timeout;
    let status = loop {
        match child.try_wait() {
            Ok(Some(s)) => break s,
            Ok(None) => {
                if Instant::now() >= deadline {
                    kill_process(&mut child);
                    let _ = reader.join();
                    return Err(format!("{program} timed out"));
                }
                std::thread::sleep(Duration::from_millis(50));
            }
            Err(e) => {
                kill_process(&mut child);
                return Err(format!("{program}: {e}"));
            }
        }
    };

    let (out, err) = reader.join().map_err(|_| format!("{program}: reader thread"))?;
    if status.success() {
        Ok(String::from_utf8_lossy(&out).trim().to_string())
    } else {
        let err = String::from_utf8_lossy(&err);
        Err(format!("{program} failed: {}", err.chars().take(300).collect::<String>()))
    }
}

pub fn short_id(url: &str) -> String {
    let mut h: u64 = 0xcbf29ce484222325;
    for b in url.bytes() {
        h ^= b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    format!("rv_{:012x}", h)
}