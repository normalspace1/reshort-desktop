import os
from pathlib import Path

# AppData/Roaming path
appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~/.config'))
reshort_dir = Path(appdata_dir) / "Reshort"

class Settings:
    server_url = os.environ.get('REVOICE_SERVER_URL', "http://localhost:3000")

    # Storage paths
    reshort_root = reshort_dir
    projects_root = (reshort_dir / "projects").resolve()
    models_root = (reshort_dir / "models").resolve()

    # Local audio separation
    sep_model_file = "Kim_Vocal_2.onnx"

    # Local speech speed stretching & mixing (never slow down speech below 1.0)
    min_rate = 1.0
    max_rate = 1.35

    # TTS provider (local sovits or server-backed)
    tts_provider = os.environ.get('TTS_PROVIDER', "fish")
    sovits_url = os.environ.get('SOVITS_URL', "http://localhost:9880")
    fish_voice_id = "default_voice_id"

def get_settings():
    return Settings()
