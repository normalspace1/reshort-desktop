use std::sync::OnceLock;

use serde::Deserialize;

#[derive(Deserialize, Clone)]
pub struct Config {
    pub ffmpeg_url: String,
    pub ytdlp_url: String,
    pub model_url: String,
    pub worker_url: String,
    pub server_url: String,
}

static CFG: OnceLock<Config> = OnceLock::new();

pub fn get() -> &'static Config {
    CFG.get_or_init(|| {
        serde_json::from_str(include_str!("../config.json")).expect("embedded config.json is invalid")
    })
}