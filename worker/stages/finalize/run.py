import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from worker.context import ProjectContext, ff
from worker.context import run as run_cmd


def _probe(src: Path, key: str) -> str:
    r = subprocess.run([ff('ffprobe'), '-v', 'error',
                        '-select_streams', 'v:0',
                        '-show_entries', f'stream={key}',
                        '-of', 'csv=p=0', str(src)],
                       capture_output=True, text=True)
    return r.stdout.strip()


def _probe_duration(src: Path) -> float:
    try:
        return float(_probe(src, 'duration'))
    except ValueError:
        raise RuntimeError(f'ffprobe could not read duration from {src}') from None


import json
import random

def _build_srt(ctx: ProjectContext) -> Path | None:
    plan_path = ctx.transcript / 'plan_flow.json'
    timing_path = ctx.transcript / 'timing.json'
    if not plan_path.exists() or not timing_path.exists():
        return None
        
    plan = json.loads(plan_path.read_text(encoding='utf-8'))['plan']
    timing = json.loads(timing_path.read_text(encoding='utf-8'))
    
    srt_orig_lines = []
    srt_trans_lines = []
    
    for idx, p in enumerate(plan):
        t = timing[p['i']]
        start = p['start']
        end = start + p['eff_len']
        
        def format_ts(sec: float) -> str:
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = int(sec % 60)
            ms = int((sec % 1) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
            
        trans_text = t['text']
        # Strip all tags like [neutral]
        import re
        trans_text = re.sub(r'\[.*?\]', '', trans_text).strip()
        orig_text = t.get('orig_text', trans_text).strip()
            
        ts_line = f"{format_ts(start)} --> {format_ts(end)}"
        
        srt_orig_lines.append(f"{idx + 1}\n{ts_line}\n{orig_text}\n")
        srt_trans_lines.append(f"{idx + 1}\n{ts_line}\n{trans_text}\n")
        
    out_trans = ctx.final / 'translate.srt'
    out_trans.write_text('\n'.join(srt_trans_lines), encoding='utf-8')
    
    out_orig = ctx.final / 'orig.srt'
    out_orig.write_text('\n'.join(srt_orig_lines), encoding='utf-8')

    # Also build styled ASS subtitles for Shorts (centered, bold, yellow with black stroke)
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,52,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,40,40,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ass_events = []
    for p in plan:
        t = timing[p['i']]
        start = p['start']
        end = start + p['eff_len']

        def format_ass_ts(sec: float) -> str:
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = int(sec % 60)
            cs = int((sec % 1) * 100)
            return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"

        text = t['text']
        import re
        text = re.sub(r'\[.*?\]', '', text).strip()
        # Clean line breaks if too long
        words = text.split()
        if len(words) > 7:
            mid = len(words) // 2
            text = ' '.join(words[:mid]) + '\\N' + ' '.join(words[mid:])
        ass_events.append(f"Dialogue: 0,{format_ass_ts(start)},{format_ass_ts(end)},Default,,0,0,0,,{text.upper()}")

    out_ass = ctx.final / 'translate.ass'
    out_ass.write_text(ass_header + '\n'.join(ass_events), encoding='utf-8')
    
    return out_ass


def _video_filter(width: int, height: int, crop: str | None, uniquify: bool, sub_path: Path | None) -> str:
    """Build vf: optional crop, fit, uniquify, and subtitles."""
    parts = [f'crop={crop}'] if crop else []
    parts.append('scale=1080:1920:force_original_aspect_ratio=decrease')
    parts.append('pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black')
    
    if uniquify:
        c = round(random.uniform(1.02, 1.06), 3)
        s = round(random.uniform(1.02, 1.08), 3)
        b = round(random.uniform(0.005, 0.02), 3)
        parts.append(f'eq=contrast={c}:saturation={s}:brightness={b}')
        parts.append('noise=alls=1:allf=t')
        
    if sub_path:
        # FFMPEG requires escaping for Windows paths in subtitles filter: C\:\\path\\to\\sub.ass
        escaped_path = str(sub_path.resolve()).replace('\\', '/').replace(':', '\\:')
        parts.append(f"subtitles='{escaped_path}'")
        
    return ','.join(parts)


def run(ctx: ProjectContext, options: dict) -> dict:
    mix = ctx.tracks / 'mix_mastered.wav'
    src = ctx.src_video
    out = ctx.final / 'final_video.mp4'
    dur = float(options.get('duration', 0) or 0) or \
        float(ctx.load_stage_result('download').get('duration') or 0) or \
        _probe_duration(src)

    w = int(options.get('video_width') or _probe(src, 'width') or 1080)
    h = int(options.get('video_height') or _probe(src, 'height') or 1920)
    
    uniquify = bool(options.get('uniquify', False))
    generated_sub_path = _build_srt(ctx)
    burn_subs = bool(options.get('burn_subtitles', options.get('subtitles', False)))
    sub_path = generated_sub_path if burn_subs else None
    
    vf = _video_filter(w, h, options.get('crop'), uniquify, sub_path)

    cmd = [ff(), '-y', '-i', str(src), '-i', str(mix),
             '-filter_complex', f'[0:v]{vf}[v]',
             '-map', '[v]', '-map', '1:a',
             '-af', f'apad=whole_dur={dur:.3f}',
             '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-profile:v', 'high',
             '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '320k',
             '-movflags', '+faststart', '-t', f'{dur:.3f}']
             
    if uniquify:
        cmd.extend(['-map_metadata', '-1'])
        
    cmd.append(str(out))
    run_cmd(cmd)

    result = {'final': out.name, 'size_mb': round(out.stat().st_size / 1e6, 1)}
    ctx.save_stage_result('finalize', result)
    return result