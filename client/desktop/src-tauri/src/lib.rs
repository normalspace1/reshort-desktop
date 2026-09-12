mod commands;
mod config;
mod services;
mod state;
mod utils;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let state = state::AppState::new();
    state.ensure_storage();
    if let Err(e) = services::worker::spawn(&state) {
        log::warn!("worker failed to start: {e}");
    }

    tauri::Builder::default()
        .manage(state)
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::settings::storage_paths,
            commands::settings::open_path,
            commands::worker::spawn_worker,
            commands::worker::worker_health,
            commands::setup::preflight_check,
            commands::setup::preflight_retry,
            commands::setup::preflight_progress,
            commands::setup::setup_start,
            commands::projects::fetch_video_info,
            commands::projects::start_generation,
            commands::projects::get_project_status,
            commands::projects::list_projects,
            commands::projects::get_video_url,
            commands::projects::delete_project,
            commands::projects::open_project_folder,
            commands::projects::clear_projects,
            commands::projects::pick_video_file,
            commands::projects::pick_video_folder,
            commands::projects::scan_folder_videos,
            commands::projects::start_local_generation,
            commands::projects::start_batch_generation,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|_, _| {});
}