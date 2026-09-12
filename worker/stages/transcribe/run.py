import io
import json
import sys
import subprocess
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import httpx

from worker.context import ProjectContext, ff
from worker.context import run as run_cmd

WIN = 15.0      # seconds per independent window (groq free tier ok: 25MB/file)
STEP = 10.0     # window offset (overlap = WIN - STEP)
EDGE = 0.4      # how many seconds inside window edges are treated as unreliable


def ensure_audio(ctx: ProjectContext):
    """Extract transcription/separation WAVs from the already-downloaded video.

    The worker never downloads video — it only transforms local files.
    """
    a16 = ctx.transcript / 'dictator.wav'
    a44 = ctx.transcript / 'dictator_hq.wav'
    if a16.exists() and a44.exists():
        return

    video = ctx.src_video
    if a16.exists() is False:
        run_cmd([ff(), '-y', '-i', str(video), '-vn', '-ac', '1', '-ar', '16000',
                 '-c:a', 'pcm_s16le', str(a16)])
    if a44.exists() is False:
        run_cmd([ff(), '-y', '-i', str(video), '-vn', '-ac', '2', '-ar', '44100',
                 '-c:a', 'pcm_s16le', str(a44)])


def _read_wav(path: Path) -> tuple[bytes, int, int]:
    with wave.open(str(path), 'rb') as w:
        sr = w.getframerate()
        n = w.getnframes()
        raw = w.readframes(n)
    return raw, sr, w.getsampwidth()


def _transcribe_window(settings, chunk_bytes: bytes, sr: int, sampwidth: int, language):
    """Transcribe one ~15s window via server (which owns the Groq key)."""
    # wav header for the chunk with same params as source
    n_frames = len(chunk_bytes) // sampwidth
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(sampwidth)
        w.setframerate(sr)
        w.writeframes(chunk_bytes)
    buf.seek(0)

    data = {
        'response_format': 'verbose_json',
        'timestamp_granularities[]': 'word',
        'temperature': '0.0',
    }
    if language:
        data['language'] = language

    files = {'file': ('window.wav', buf, 'audio/wav')}
    r = httpx.post(settings.server_url.rstrip('/') + '/llm/transcribe', data=data,
                   files=files, timeout=180)
    if r.status_code != 200:
        raise RuntimeError(f'LLM server HTTP {r.status_code}: {r.text[:200]}')
    return r.json()


def run(ctx: ProjectContext, options: dict) -> dict:
    settings = ctx.settings
    if not settings.server_url:
        raise RuntimeError('SERVER_URL not configured — all LLM calls go through the server')

    ensure_audio(ctx)

    raw, sr, sampwidth = _read_wav(ctx.transcript / 'dictator.wav')
    total = len(raw) // sampwidth / sr  # seconds (mono)

    # Word timestamps via windowed API calls. Each window is transcribed
    # independently (no condition-on-previous) to avoid whisper hallucination
    # on long files; overlapping copies get merged by «deepest inside window».
    words = []          # (start, end, text, reliability, win_start)
    info = None
    pos = 0.0
    while pos < total:
        end = min(pos + WIN, total)
        n0 = int(pos * sr) * sampwidth
        n1 = int(end * sr) * sampwidth
        chunk = raw[n0:n1]
        try:
            js = _transcribe_window(settings, chunk, sr, sampwidth,
                                    options.get('language'))
        except Exception as e:      # stage must never die on one bad window
            print(f'[transcribe] window {pos:.0f}s failed: {e}')
            pos += STEP
            continue
        if info is None:
            info = {'language': js.get('language')}

        words_arr = js.get('words')
        if words_arr:
            for w in words_arr:
                w_start = pos + w['start']
                w_end = pos + w['end']
                rel = min(w['start'] - EDGE, WIN - w['end'])
                words.append((w_start, w_end, (w.get('word') or '').strip(), rel, pos))
        else:
            for seg in (js.get('segments') or []):
                w_start = pos + seg['start']
                w_end = pos + seg['end']
                rel = min(seg['start'] - EDGE, WIN - seg['end'])
                words.append((w_start, w_end, (seg.get('text') or '').strip(), rel, pos))
        pos += STEP

    # Merge overlapping window copies: prefer the copy deepest inside its window.
    words = [w for w in words if w[2]]
    words.sort(key=lambda x: (round(x[0], 3), -x[3]))
    kept = []
    for w in words:
        if not kept or w[0] >= kept[-1][1] - 0.03:
            kept.append(w)

    # Rebuild whisper-like segments: word gap > 0.6s starts a new segment.
    out = []
    for w in kept:
        start, end, txt = w[0], w[1], w[2]
        word = {'w': txt, 's': round(start, 3), 'e': round(end, 3)}
        if not out or start - out[-1]['end'] > 0.6:
            out.append({'start': round(start, 3), 'end': round(end, 3),
                        'text': '', 'words': [word]})
        else:
            out[-1]['words'].append(word)
            out[-1]['end'] = round(end, 3)
    for s in out:
        s['text'] = (' '.join(x['w'] for x in s['words'])).strip()

    (ctx.transcript / 'whisper_words.json').write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')

    lang = (info or {}).get('language') or options.get('language')
    result = {
        'segments': len(out),
        'lang': lang,
        'provider': 'server',
    }
    ctx.save_stage_result('transcribe', result)
    return result