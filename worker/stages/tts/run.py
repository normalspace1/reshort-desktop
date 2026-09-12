import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import httpx

from worker.context import ProjectContext, ff


import base64
import tempfile

def probe(path: Path) -> float:
    r = subprocess.run([ff('ffprobe'), '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=noprint_wrappers=1:nokey=1', str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        raise RuntimeError(
            f'ffprobe could not read duration from {path}: {r.stderr.strip()[:200]}'
        ) from None

def _get_reference_data(ctx: ProjectContext, start: float, end: float, orig_text: str) -> tuple[str, str] | tuple[None, None]:
    if not orig_text.strip():
        return None, None
    cands = list(ctx.stems.glob('*Vocals*.wav'))
    audio_src = cands[0] if cands else ctx.transcript / 'dictator_hq.wav'
    
    pad_s = max(0, start - 0.1)
    pad_e = end + 0.1
    
    # Require at least 2.5 seconds for cloning, pad if necessary
    if pad_e - pad_s < 2.5:
        pad_e = pad_s + 2.5
        
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        tmp_name = tmp.name
        
    r = subprocess.run([ff('ffmpeg'), '-y', '-v', 'error', '-i', str(audio_src), '-ss', str(pad_s), '-to', str(pad_e), 
             '-c:a', 'pcm_s16le', '-ar', '44100', '-ac', '1', tmp_name])
    if r.returncode != 0:
        os.unlink(tmp_name)
        raise RuntimeError(f'reference audio extract failed: {r.stderr[-300:]}'.strip())
    return tmp_name, orig_text

def _resolve_voice(voice_name: str | None) -> str:
    if not voice_name:
        return 'ru-RU-DmitryNeural'
    v = str(voice_name).lower()
    if 'svetlana' in v or 'female' in v or 'жен' in v:
        return 'ru-RU-SvetlanaNeural'
    return 'ru-RU-DmitryNeural'


def _gen_one(index: int, text: str, out_file: Path, settings, speed: float = 1.0, ref_audio_path: str | None = None, ref_text: str | None = None, voice: str = 'ru-RU-DmitryNeural') -> tuple[int, str, str]:
    try:
        if settings.tts_provider == 'sovits':
            payload = {
                "text": text,
                "text_lang": "ru",
                "prompt_text": ref_text or "",
                "prompt_lang": "en",
                "ref_audio_path": ref_audio_path or "",
                "speed_factor": round(speed, 3),
            }

            for attempt in range(3):
                try:
                    with httpx.stream('POST', settings.sovits_url.rstrip('/') + '/tts',
                                      json=payload, timeout=300) as r:
                        if r.status_code != 200:
                            r.read()
                            return index, f'error HTTP {r.status_code}', r.text[:120]
                        with open(out_file, 'wb') as f:
                            for chunk in r.iter_bytes():
                                f.write(chunk)
                    return index, 'ok', ''
                except Exception as e:
                    if attempt == 2:
                        return index, 'exc', str(e)[:120]
                    time.sleep(2)
            return index, 'exc', 'loop-exhausted'
            
        else:
            # Fish Audio
            if not settings.server_url:
                return index, 'skip', 'SERVER_URL not configured'
                
            payload = {'text': text, 'reference_id': settings.fish_voice_id,
                       'format': 'wav', 'sample_rate': 44100}
            
            if ref_audio_path and ref_text:
                with open(ref_audio_path, 'rb') as f:
                    payload['reference_audio'] = base64.b64encode(f.read()).decode('utf-8')
                payload['reference_text'] = ref_text
                
            if abs(speed - 1.0) > 1e-3:
                payload['prosody'] = {'speed': round(speed, 3)}

            for attempt in range(3):
                try:
                    with httpx.stream('POST', settings.server_url.rstrip('/') + '/llm/tts',
                                      json=payload, timeout=300) as r:
                        if r.status_code != 200:
                            break
                        with open(out_file, 'wb') as f:
                            for chunk in r.iter_bytes():
                                f.write(chunk)
                    return index, 'ok', ''
                except Exception as e:
                    if attempt == 2:
                        break
                    time.sleep(2)

            # Fallback to Edge-TTS if Fish Audio is unavailable or out of credits
            try:
                import asyncio
                import edge_tts
                rate_pct = int(round((speed - 1.0) * 100))
                rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"
                tmp_mp3 = out_file.with_suffix('.mp3')
                resolved_voice = _resolve_voice(voice)
                asyncio.run(edge_tts.Communicate(text, resolved_voice, rate=rate_str).save(str(tmp_mp3)))
                if tmp_mp3.exists() and tmp_mp3.stat().st_size > 0:
                    # Convert to target wav format with ffmpeg
                    subprocess.run([ff('ffmpeg'), '-y', '-v', 'error', '-i', str(tmp_mp3),
                                    '-ar', '44100', '-ac', '1', '-c:a', 'pcm_s16le', str(out_file)], check=True)
                    tmp_mp3.unlink(missing_ok=True)
                    return index, 'ok', ''
            except Exception as edge_err:
                print(f"[warning] edge_tts fallback failed: {edge_err}")

            return index, 'exc', 'tts-failed'
    finally:
        if ref_audio_path and Path(ref_audio_path).exists():
            Path(ref_audio_path).unlink(missing_ok=True)


def _phrases_speeds(timing) -> list[float]:
    """Per-phrase prosody speed so TTS length matches its subtitle slot."""
    speeds = []
    for i, p in enumerate(timing):
        nxt = timing[i + 1]['start'] if i + 1 < len(timing) else p['end']
        slot = max(nxt - p['start'], 0.4)
        dur = p.get('dur') or (p['end'] - p['start'])
        frame = dur / slot
        clamp = min(max(frame, 1.0), 1.35)
        speeds.append(clamp)
    return speeds


def _slot_of(timing, i: int) -> float:
    if i + 1 < len(timing):
        return max(timing[i + 1]['start'] - timing[i]['start'], 0.4)
    return max(timing[i]['end'] - timing[i]['start'], 0.4)


def _fit_speed(dur: float, slot: float, prev_speed: float) -> float:
    """Proposed prosody.speed for next run so dur ~= slot."""
    return min(max(prev_speed * (dur / max(slot, 0.4)), 1.0), 1.35)


def _extract_original_phrase(ctx: ProjectContext, start: float, end: float, out_file: Path) -> tuple[int, str, str]:
    # Always use the original untouched audio for memes to preserve the exact sound, reverb, and background
    audio_src = ctx.transcript / 'dictator_hq.wav'
    fade_st = round(end - start - 0.05, 3)
    duration = round(end - start, 3)
    res = subprocess.run([ff('ffmpeg'), '-y', '-v', 'warning', '-ss', str(start), '-t', str(duration), '-i', str(audio_src), 
             '-af', f'afade=t=in:st=0:d=0.05,afade=t=out:st={fade_st}:d=0.05',
             '-c:a', 'pcm_s16le', '-ar', '44100', '-ac', '1', str(out_file)], capture_output=True, text=True)
    if res.returncode != 0:
        return 0, 'error', res.stderr
    return 0, 'ok', ''

def _generate(timing, gmap, ctx, workers, options, only: list[int] | None = None) -> list[tuple]:
    status = []
    idxs = list(range(len(timing))) if only is None else only
    keep_memes = options.get('keep_memes', False)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {}
        for i in idxs:
            p = timing[i]
            is_meme = keep_memes and p['text'].strip() and p['text'].strip() == p.get('orig_text', '').strip()
            
            if is_meme:
                f = ex.submit(_extract_original_phrase, ctx, p['start'], p['end'], ctx.phrases / f'ph{i:02d}.wav')
                # Modify return to match _gen_one signature
                futs[f] = i
            else:
                ref_audio, ref_text = _get_reference_data(ctx, p['start'], p['end'], p.get('orig_text', ''))
                f = ex.submit(_gen_one, i, p['text'], ctx.phrases / f'ph{i:02d}.wav',
                              ctx.settings, gmap[i], ref_audio, ref_text, options.get('voice', 'ru-RU-DmitryNeural'))
                futs[f] = i
            
        for f in as_completed(futs):
            idx = futs[f]
            res = f.result()
            # _extract_original_phrase returns 0 for index, so we overwrite with actual idx
            status.append((idx, res[1], res[2]))
    return status


def run(ctx: ProjectContext, options: dict) -> dict:
    timing = json.loads((ctx.transcript / 'timing.json').read_text(encoding='utf-8'))
    
    workers = int(options.get('concurrency', 4))
    n = len(timing)

    # 1. Generate all phrases at energetic base speed (1.12 = +12% for lively Shorts tempo)
    base_speed = float(options.get('tts_base_speed', 1.12))
    gmap = [base_speed] * n
    status = _generate(timing, gmap, ctx, workers, options)
    failed = [s for s in status if s[1] != 'ok']
    if failed:
        raise RuntimeError(f'tts failures: {failed}')

    # 2. Trim silence so they start exactly on time
    from worker.stages.mix.run import trim_silence
    keep_memes = options.get('keep_memes', False)
    for i in range(n):
        p = timing[i]
        is_meme = keep_memes and p['text'].strip() and p['text'].strip() == p.get('orig_text', '').strip()
        if not is_meme:
            trim_silence(ctx.phrases / f'ph{i:02d}.wav')

    # 3. Measure actual durations
    durs = [probe(ctx.phrases / f'ph{i:02d}.wav') for i in range(n)]

    # 4. 2-Pass Native Speed Adjustment:
    # Only speed up phrases that overflow their slot.
    # NEVER slow down below base_speed (keep lively, energetic pacing and natural pauses).
    redo = []
    for i in range(n):
        p = timing[i]
        is_meme = keep_memes and p['text'].strip() and p['text'].strip() == p.get('orig_text', '').strip()
        if is_meme:
            continue
            
        slot = _slot_of(timing, i)
        dur = durs[i]
        
        # If phrase duration exceeds the available slot, speed it up to fit
        if dur > slot * 1.02:
            needed_speed = (dur / max(slot, 0.4)) * gmap[i]
            new_speed = min(max(needed_speed, base_speed), 1.40)
            if new_speed > gmap[i] * 1.03:
                gmap[i] = round(new_speed, 3)
                redo.append(i)

    if redo:
        print(f"TTS 2-pass: Re-generating phrases {redo} with native speeds: {[gmap[i] for i in redo]}")
        status = _generate(timing, gmap, ctx, workers, options, only=redo)
        failed = [s for s in status if s[1] != 'ok']
        if failed:
            raise RuntimeError(f'tts 2-pass failures: {failed}')
            
        for i in redo:
            trim_silence(ctx.phrases / f'ph{i:02d}.wav')
            durs[i] = probe(ctx.phrases / f'ph{i:02d}.wav')

    for p, d in zip(timing, durs):
        p['dur'] = d
    for p, sp in zip(timing, gmap):
        p['speed'] = sp
    (ctx.transcript / 'timing.json').write_text(json.dumps(timing, ensure_ascii=False, indent=1), encoding='utf-8')

    result = {'phrases': n, 'durations': durs, 'sum': round(sum(durs), 3),
              'speeds': gmap, 'voice_id': ctx.settings.fish_voice_id, 'redo': []}
    ctx.save_stage_result('tts', result)
    return result