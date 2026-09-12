import json
import sys
import threading
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from worker.main import run_pipeline
from worker.settings import get_settings

app = FastAPI(title="ReShort Worker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VideoRequest(BaseModel):
    url: str
    project_id: str | None = None
    keep_memes: bool = True
    uniquify: bool = True
    adapt_tts: bool = True
    voice_id: str | None = None
    voice: str | None = None
    tts_base_speed: float | None = None
    burn_subtitles: bool = True


# Simple in-memory task tracker (project.json holds the authoritative state)
tasks_db = {}
_lock = threading.Lock()


def process_video_task(
    project_id: str,
    url: str,
    keep_memes: bool,
    uniquify: bool,
    adapt_tts: bool,
    voice_id: str | None,
    voice: str | None = None,
    tts_base_speed: float | None = None,
    burn_subtitles: bool = True,
):
    with _lock:
        tasks_db[project_id] = {"status": "processing", "message": "Обработка видео (это может занять пару минут)..."}

    options = {
        'url': url,
        'keep_memes': keep_memes,
        'uniquify': uniquify,
        'adapt_tts': adapt_tts,
        'target_lang': 'ru',
        'burn_subtitles': burn_subtitles,
    }
    if voice_id:
        options['voice_id'] = voice_id
    if voice:
        options['voice'] = voice
    if tts_base_speed is not None:
        options['tts_base_speed'] = tts_base_speed

    try:
        run_pipeline(project_id, options)
        video_path = get_settings().projects_root / project_id / 'output' / 'final_video.mp4'
        if video_path.exists():
            with _lock:
                tasks_db[project_id] = {"status": "done", "video_path": str(video_path)}
            print(f"✅ Success! Video saved to {video_path}")
        else:
            with _lock:
                tasks_db[project_id] = {"status": "error", "message": "Файл не найден после генерации"}
    except Exception as e:
        with _lock:
            tasks_db[project_id] = {"status": "error", "message": str(e)}
        print(f"❌ Error processing video: {e}")


@app.post("/api/generate")
async def generate_video(req: VideoRequest, background_tasks: BackgroundTasks):
    if not req.project_id:
        return {"status": "error", "message": "project_id required (video is downloaded by the Tauri backend)"}
    background_tasks.add_task(
        process_video_task,
        req.project_id,
        req.url,
        req.keep_memes,
        req.uniquify,
        req.adapt_tts,
        req.voice_id,
        req.voice,
        req.tts_base_speed,
        req.burn_subtitles,
    )
    return {"status": "started", "project_id": req.project_id}


@app.get("/api/status/{project_id}")
async def get_status(project_id: str):
    with _lock:
        t = tasks_db.get(project_id)
    if t:
        return t
    # Fallback to the authoritative project.json so status survives a worker restart.
    p = get_settings().projects_root / project_id / 'project.json'
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            return {
                'status': data.get('status'),
                'current_stage': data.get('current_stage'),
                'message': data.get('message'),
            }
        except Exception:
            pass
    return {"status": "unknown"}


@app.get("/api/video/{project_id}")
async def get_video(project_id: str):
    video_path = get_settings().projects_root / project_id / 'output' / 'final_video.mp4'
    if video_path.exists():
        return FileResponse(str(video_path), media_type="video/mp4")
    return {"error": "Video not found"}


@app.get("/api/thumbnail/{project_id}")
async def get_thumbnail(project_id: str):
    thumb = get_settings().projects_root / project_id / 'input' / 'thumb.jpg'
    if thumb.exists():
        return FileResponse(str(thumb), media_type="image/jpeg")
    return {"error": "Thumbnail not found"}


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "ReShort Worker"}


if __name__ == "__main__":
    print("Starting ReShort Worker API on port 8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000)