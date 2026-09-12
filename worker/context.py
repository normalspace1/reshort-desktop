import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from worker.settings import get_settings
FFMPEG_BIN = Path(os.environ.get('FFMPEG_BIN', '')).expanduser() if os.environ.get('FFMPEG_BIN') else None


def _candidates(name: str) -> list[str]:
    if os.name == 'nt':
        return [name + '.exe', name]
    return [name, name + '.exe']


def _known_bin_dirs() -> list[Path]:
    global _CACHED_BIN_DIRS
    if _CACHED_BIN_DIRS is not None:
        return _CACHED_BIN_DIRS

    dirs = []
    if FFMPEG_BIN is not None:
        dirs.append(FFMPEG_BIN)

    if os.name == 'nt':
        try:
            s = get_settings()
            if s.data_dir:
                reshort_bin = Path(s.data_dir) / 'bin'
                if reshort_bin.is_dir():
                    dirs.append(reshort_bin)
        except Exception:
            pass
        appdata = os.environ.get('APPDATA')
        if appdata:
            reshort_bin = Path(appdata) / 'Reshort' / 'bin'
            if reshort_bin.is_dir() and reshort_bin not in dirs:
                dirs.append(reshort_bin)

        local = os.environ.get('LOCALAPPDATA')
        if local:
            winget = Path(local) / 'Microsoft' / 'WinGet' / 'Packages'
            if winget.is_dir():
                for d in sorted(winget.rglob('ffmpeg.exe')):
                    dirs.append(d.parent)
    else:
        dirs += [Path('/usr/local/bin'), Path('/usr/bin'), Path('/opt/ffmpeg/bin')]

    _CACHED_BIN_DIRS = dirs
    return dirs


_CACHED_BIN_DIRS: list[Path] | None = None


def _find_ff(name: str) -> str:
    for exe in _candidates(name):
        found = shutil.which(exe)
        if found:
            return found
        for d in _known_bin_dirs():
            cand = d / exe
            if cand.exists():
                return str(cand)
    raise FileNotFoundError(f'{name} not found in PATH (set FFMPEG_BIN to its containing folder)')


def ff(name: str = 'ffmpeg') -> str:
    return _find_ff(name)


def ff_bin_dir() -> Path:
    p = Path(ff('ffmpeg'))
    if p.name.lower() in ('ffmpeg', 'ffmpeg.exe'):
        return p.parent
    return p


def run(cmd, check=True, **kw):
    _debug_append('$ ' + ' '.join(str(c) for c in cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.stdout:
        _debug_append('[out] ' + r.stdout[-3000:])
    if r.stderr:
        _debug_append('[err] ' + r.stderr[-3000:])
    if check and r.returncode != 0:
        raise RuntimeError(f'command failed rc={r.returncode}: {" ".join(str(c) for c in cmd)[:200]}')
    return r


_DEBUG_LOG_PATH: Path | None = None


def set_debug_log(path: Path | None):
    global _DEBUG_LOG_PATH
    _DEBUG_LOG_PATH = path
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(f'\n===== session {__import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime())} =====\n')


def _debug_append(line: str):
    if _DEBUG_LOG_PATH is None:
        return
    try:
        with open(_DEBUG_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


class ProjectContext:
    """Filesystem layout for one project under storage/projects/{project_id}."""

    def __init__(self, project_id: str, settings=None):
        self.settings = settings or get_settings()
        self.id = project_id
        self.root = self.settings.projects_root / project_id
        
        # Dataset-friendly, clean directory structure
        self.source = self.root / 'input'
        self.transcript = self.root / 'dataset'
        self.phrases = self.transcript / 'audio_tts'
        self.tracks = self.root / 'temp'
        self.final = self.root / 'output'
        self.stems = self.tracks / 'stems'
        self.mdx_models = self.tracks / 'mdx_models'
        self.debug_dir = self.root / 'logs'
        
        for d in (self.source, self.transcript, self.phrases, self.tracks, self.final, self.stems, self.mdx_models, self.debug_dir):
            d.mkdir(parents=True, exist_ok=True)

    def debug_log(self, stage: str) -> Path:
        # Centralized logging: all stages write to a single pipeline.log
        log_file = self.debug_dir / 'pipeline.log'
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f'\n\n[=== STAGE: {stage.upper()} ===]\n')
        return log_file

    @property
    def src_video(self) -> Path:
        for cand in ('src.f616.mp4', 'video_original.mp4', 'src.mp4', 'src.webm'):
            p = self.source / cand
            if p.exists():
                return p
        raise FileNotFoundError(f'no source video in {self.source}')

    def save_stage_result(self, stage: str, data: dict):
        (self.root / f'{stage}_result.json').write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')

    def load_stage_result(self, stage: str) -> dict:
        p = self.root / f'{stage}_result.json'
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding='utf-8'))

    @property
    def max_rate(self) -> float:
        return float(self.settings.max_rate)