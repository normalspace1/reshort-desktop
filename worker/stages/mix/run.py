import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from worker.context import ProjectContext, ff
from worker.context import run as run_cmd


def build_voice(ctx: ProjectContext, plan, T):
    inputs, filters = [], []
    for i, p in enumerate(plan):
        f = ctx.phrases / f'ph{i:02d}.wav'
        inputs += ['-i', str(f)]
        ms = int(p['start'] * 1000)
        
        rate = float(p.get('rate', 1.0))
        
        if abs(rate - 1.0) > 0.001:
            filters.append(f'[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo,atempo={rate:.4f},'
                           f'adelay={ms}|{ms},apad=whole_dur={T:.3f}[v{i}]')
        else:
            filters.append(f'[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo,'
                           f'adelay={ms}|{ms},apad=whole_dur={T:.3f}[v{i}]')
    mixlabels = ''.join(f'[v{i}]' for i in range(len(plan)))
    filters.append(mixlabels + f'amix=inputs={len(plan)}:normalize=0,atrim=0:{T:.3f}[a]')

    out = ctx.tracks / 'voice_track_flow.wav'
    run_cmd([ff(), '-y', *inputs, '-filter_complex', ';'.join(filters),
             '-map', '[a]', '-c:a', 'pcm_s16le', '-ar', '44100', str(out)])


def mix_audio(ctx: ProjectContext, stem_db: float | None, stem_file: Path):
    voice = ctx.tracks / 'voice_track_flow.wav'
    out = ctx.tracks / 'mix_mastered.wav'
    
    if stem_db is None or stem_db < -45:
        # Just voice, master it to -14 LUFS
        run_cmd([ff(), '-y', '-i', str(voice),
                 '-af', 'loudnorm=I=-14:LRA=11:TP=-1.5',
                 '-c:a', 'pcm_s16le', '-ar', '44100', str(out)])
    else:
        # Sidechain ducking + Mastering
        vol = max(min(1.2, 10 ** ((-16 - stem_db) / 20)), 0.2)
        
        filter_str = (
            f'[0:a]volume={vol:.3f}[bg_vol];'
            f'[1:a]volume=1.0,asplit=2[v_vol1][v_vol2];'
            f'[bg_vol][v_vol1]sidechaincompress=threshold=0.1:ratio=3:attack=10:release=200[bg_ducked];'
            f'[bg_ducked][v_vol2]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,loudnorm=I=-14:LRA=11:TP=-1.5[a]'
        )
        
        run_cmd([ff(), '-y', '-i', str(stem_file), '-i', str(voice),
                 '-filter_complex', filter_str,
                 '-map', '[a]', '-c:a', 'pcm_s16le', '-ar', '44100', str(out)])


def trim_silence(path: Path, out: Path | None = None):
    """Strip leading+trailing silence below -40dB so voice starts exactly on time."""
    out = out or path
    tmp = out.with_suffix('.unsilenced.wav')
    run_cmd([ff(), '-y', '-i', str(path),
             '-af', 'silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,'
                    'areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,'
                    'areverse',
             '-c:a', 'pcm_s16le', '-ar', '44100', str(tmp)])
    tmp.replace(out)


def run(ctx: ProjectContext, options: dict) -> dict:
    plan_path = ctx.transcript / 'plan_flow.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))['plan']

    # Rebuild the plan against actual TTS durations: phrases are regenerated
    # (voice switch / different reference) may run longer than the subtitle
    # windows used when the plan was built, which would make phrases overlap
    # on the timeline ("two voices on top of each other").
    from worker.stages.adapt.run import _build_plan
    from worker.stages.tts.run import probe
    timing = json.loads((ctx.transcript / 'timing.json').read_text(encoding='utf-8'))
    
    keep_memes = options.get('keep_memes', False)
    durs = []
    for i in range(len(timing)):
        p = timing[i]
        is_meme = keep_memes and p['text'].strip() and p['text'].strip() == p.get('orig_text', '').strip()
        f = ctx.phrases / f'ph{i:02d}.wav'
        if f.exists():
            if not is_meme:
                trim_silence(f)
            durs.append(probe(f))
        else:
            durs.append(0.0)
            
    for p, d in zip(timing, durs):
        p['dur'] = d
    (ctx.transcript / 'timing.json').write_text(json.dumps(timing, ensure_ascii=False, indent=1), encoding='utf-8')
    plan = _build_plan(timing, max_rate=ctx.max_rate, min_rate=ctx.settings.min_rate)
    plan_path.write_text(json.dumps({'plan': plan, 'total': round(sum(p['eff_len'] for p in plan), 3)}, indent=1), encoding='utf-8')

    T = plan[-1]['start'] + plan[-1]['eff_len']
    build_voice(ctx, plan, T)

    sep = ctx.load_stage_result('separate')
    stem_db = (sep or {}).get('stem_mean_db')
    stem_file = ctx.stems / (sep or {}).get('stem', 'dictator_(Instrumental)_UVR-MDX-NET-Inst_HQ_3.wav')
    if not stem_file.exists():
        cands = list(ctx.stems.glob('*Instrumental*.wav'))
        stem_file = cands[0] if cands else stem_file
        if stem_db is None:
            from worker.stages.separate.run import stem_mean_db
            stem_db = stem_mean_db(stem_file)
    mix_audio(ctx, stem_db, stem_file)

    result = {'voice_track': 'voice_track_flow.wav', 'mix': 'mix_mastered.wav',
              'total': round(T, 3), 'stem_mean_db': stem_db}
    ctx.save_stage_result('mix', result)
    return result