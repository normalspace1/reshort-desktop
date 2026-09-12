import json
from pathlib import Path

import httpx

from worker.context import ProjectContext


def _split_lines(words: list[dict]) -> list[dict]:
    """Group words into subtitle-style lines using word timestamps.

    Break on: long gap (>GAP), cumulative length > MAX_CHARS, duration > MAX_DUR,
    sentence punctuation (. ! ? …), comma/phrase boundary (SOFT), or segment
    boundary. Then merge short tails (<=MIN_WORDS words) back into the previous
    line so we never leave a stub like "счета." on its own.

    Keeps windows small enough that TTS rarely needs heavy slowdown.
    """
    MAX_CHARS = 100
    MAX_DUR = 7.0
    GAP = 0.8
    STRONG = set('.!?…;')

    lines = []
    cur_words = []
    cur_start = None
    cur_end = None
    cur_len = 0

    def flush():
        nonlocal cur_words, cur_start, cur_end, cur_len
        if not cur_words:
            return
        text = ' '.join(w['w'].strip() for w in cur_words).strip()
        if text:
            lines.append({'start': cur_start, 'end': cur_end, 'text': text})
        cur_words, cur_start, cur_end, cur_len = [], None, None, 0

    for i, w in enumerate(words):
        start, end = w['s'], w['e']
        txt = w['w'].strip()
        if not txt:
            continue
            
        if cur_words:
            gap = start - cur_end if cur_end is not None else 0.0
            dur = end - cur_start
            
            # Flush if there's a long silence, or we exceeded max duration, or we hit a strong punctuation AND have a decent length
            if gap > GAP:
                flush()
            elif dur > MAX_DUR:
                flush()
            elif cur_len + len(txt) + 1 > MAX_CHARS:
                flush()
            elif cur_words[-1]['w'].strip()[-1:] in STRONG and dur > 3.0:
                flush()
                
        if cur_words:
            cur_words.append(w)
            cur_end, cur_len = end, cur_len + len(txt) + 1
        else:
            cur_start, cur_end, cur_len = start, end, len(txt)
            cur_words = [w]
            
    flush()

    for ln in lines:
        ln.pop('words', None)
    return lines


def _is_noise(text: str) -> bool:
    """True for segments that are just filtered speech/noise: single repeated
    syllables or vowels ("а", "а а а а", "мм", "э э"). Such whisper hits are
    usually music/applause, not words, and should never be spoken by TTS."""
    t = text.strip().strip('.,!?…;').lower()
    if not t:
        return True
    tokens = [w for w in t.split() if w.strip('.,!?…;')]
    if not tokens:
        return True
    # every token must be a 1-2 char vowel/nasal repeat like "а", "аа", "мм", "э"
    return all(len(w) <= 2 and all(c in 'аеёиоуыэюямн' for c in w) for w in tokens)


def _build_phrases_from_segments(src) -> list[dict]:
    """MVP: one phrase per whisper segment (windows = segment timing).

    Accepts faster-whisper output (list of {start,end,text,words}) or
    openai-whisper output (dict with 'segments' key).
    """
    segments = src.get('segments', []) if isinstance(src, dict) else src
    # skip whisper noise segments (music/applause: "а", "а а а") before merging words
    segments = [s for s in segments if not _is_noise(s.get('text', ''))]
    all_words = []
    for s in segments:
        ws = s.get('words') or []
        all_words.extend(ws)
    if all_words:
        phrases = _split_lines(all_words)
        if phrases:
            phrases = [p for p in phrases if not _is_noise(p['text'])]
            return phrases
    return [{'start': s['start'], 'end': s['end'], 'text': s['text'].strip()}
            for s in segments if not _is_noise(s.get('text', ''))]


def _llm_translate(texts: list[str], target_lang: str, server_url: str, keep_memes: bool = False) -> list[str]:
    """Translate phrase texts via the server."""
    if not server_url:
        raise RuntimeError('SERVER_URL not configured, cannot translate')

    payload = {
        'texts': texts,
        'target_lang': target_lang,
        'keep_memes': keep_memes,
    }
    r = httpx.post(server_url.rstrip('/') + '/llm/translate', json=payload, timeout=180)
    r.raise_for_status()
    out = (r.json() or {}).get('results')
    if not isinstance(out, list) or not all(isinstance(x, str) for x in out):
        print('[warning] translate response shape unexpected, keeping originals')
        return texts
    if len(out) < len(texts):
        out = out + texts[len(out):]
    return out[:len(texts)]


def _is_cyrillic(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return True
    cyr = sum(1 for c in letters if '\u0400' <= c <= '\u04FF')
    return cyr / len(letters) >= 0.3


def _llm_adapt_tts(texts: list[str], server_url: str, keep_memes: bool = False) -> list[str]:
    """Make TTS-safe text via the server."""
    if not server_url:
        raise RuntimeError('SERVER_URL not configured (needed for adapt_tts)')

    payload = {
        'texts': texts,
        'keep_memes': keep_memes,
    }
    r = httpx.post(server_url.rstrip('/') + '/llm/adapt', json=payload, timeout=240)
    try:
        r.raise_for_status()
        out = r.json().get('results') or texts
        if len(out) < len(texts):
            out = out + texts[len(out):]   # fallback for any missing lines
        return out[:len(texts)]
    except Exception as e:
        print(f"[warning] adapt failed: {e}")
        return texts


def _build_plan(phrases, max_rate: float, min_rate: float = 1.0,
                target_duration: float | None = None, hard_max: float = 2.0) -> list[dict]:
    """start = line start; rate in [min_rate, max_rate].

    Speech is never slowed down below 1.0 (so voice remains energetic and punchy).
    If speech is longer than the slot, it is sped up smoothly up to max_rate.
    """

    def make(mr: float) -> list[dict]:
        prev_end = 0.0
        plan = []
        for i, seg in enumerate(phrases):
            nxt_start = phrases[i + 1]['start'] if i + 1 < len(phrases) else seg['end']
            slot = (nxt_start - seg['start']) or (seg['end'] - seg['start'])
            tts = seg.get('tts') or seg.get('dur', seg['end'] - seg['start'])
            rate = tts / slot if slot > 0 else 1.0
            if rate < 1.0:
                rate = 1.0  # Never slow down speech; keep energetic tempo and natural pauses
            elif rate > mr:
                rate = mr
            eff = tts / rate
            start = max(seg['start'], prev_end)
            plan.append({'i': i, 'start': round(start, 3), 'rate': round(rate, 3),
                         'eff_len': round(eff, 3), 'tts': round(tts, 3)})
            prev_end = start + eff
        return plan

    plan = make(max_rate)
    if target_duration and plan:
        end = plan[-1]['start'] + plan[-1]['eff_len']
        mr = max_rate
        while end > target_duration + 0.02 and mr < hard_max:
            mr = min(mr + 0.05, hard_max)
            plan = make(mr)
            end = plan[-1]['start'] + plan[-1]['eff_len']
    return plan


def run(ctx: ProjectContext, options: dict, durs: list[float] | None = None) -> dict:
    segments = json.loads((ctx.transcript / 'whisper_words.json').read_text(encoding='utf-8'))

    phrases = _build_phrases_from_segments(segments)
    for p in phrases:
        p['orig_text'] = p['text']

    target_lang = options.get('target_lang', 'ru')
    keep_memes = options.get('keep_memes', False)
    adapt_enabled = bool(options.get('adapt_tts', True))
    any_latin = any(not _is_cyrillic(p['text']) for p in phrases)
    
    if target_lang == 'ru' and any_latin:
        try:
            translated = _llm_translate([p['text'] for p in phrases], target_lang, ctx.settings.server_url, keep_memes)
            for p, t in zip(phrases, translated):
                p['text'] = t
        except Exception as e:
            print(f"[warning] _llm_translate failed: {e}", flush=True)
            if not adapt_enabled:
                print("[info] adapt_tts is disabled; proceeding with original transcript texts", flush=True)
            else:
                raise RuntimeError(f"Ошибка перевода (Gemini): {e}")

    print(f"ADAPT options: adapt_enabled={adapt_enabled}, keep_memes={keep_memes}", flush=True)
    if adapt_enabled:
        print("Calling _llm_adapt_tts...", flush=True)
        try:
            adapted = _llm_adapt_tts([p['text'] for p in phrases], ctx.settings.server_url, keep_memes)
            for p, t in zip(phrases, adapted):
                p['text'] = t
        except Exception as e:
            print(f"[warning] _llm_adapt_tts failed: {e}", flush=True)
            raise RuntimeError(f"Ошибка адаптации текста (Gemini): {e}")

    timing_path = ctx.transcript / 'timing.json'
    timing_path.write_text(json.dumps(phrases, ensure_ascii=False, indent=1), encoding='utf-8')

    if durs is None:
        durs = []
        from worker.stages.tts.run import probe
        for i, p in enumerate(phrases):
            f = ctx.phrases / f'ph{i:02d}.wav'
            durs.append(probe(f) if f.exists() else p['dur'] if 'dur' in p else p['end'] - p['start'])
    for p, d in zip(phrases, durs):
        p['dur'] = d

    plan = _build_plan(phrases, ctx.max_rate, ctx.settings.min_rate)
    total = plan[-1]['start'] + plan[-1]['eff_len'] if plan else 0.0
    (ctx.transcript / 'plan_flow.json').write_text(
        json.dumps({'plan': plan, 'total': round(total, 3)}, indent=1), encoding='utf-8')

    result = {'phrases': len(phrases), 'total': round(total, 3)}
    ctx.save_stage_result('adapt', result)
    return result