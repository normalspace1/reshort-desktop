"""Revoice Worker — local pipeline processor (dumb).

The worker never downloads anything and never talks to video platforms.
It only:
  1. Processes a project folder (the video is already provided by the
     Tauri/Rust backend into {root}/input/src.f616.mp4).
  2. Talks to the NestJS server (localhost:3000) for external AI calls
     (transcribe / translate / adapt / tts).

Usage (CLI, single run):
    python -m worker.main --project rv_xxx
    python -m worker.main --project rv_xxx --video path/to/video.mp4 --voice VOICE_ID

Server mode (for the Tauri/Rust backend):
    python -m worker.server
"""
import argparse
import importlib
import shutil
import sys
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from worker.settings import get_settings
from worker.context import ProjectContext, set_debug_log
from worker.state import ProjectState

STAGES = ['transcribe', 'adapt', 'separate', 'tts', 'mix', 'finalize']


def run_stage(ctx: ProjectContext, state: ProjectState, stage: str, options: dict) -> dict:
    """Run a single stage."""
    set_debug_log(ctx.debug_log(stage))
    state.set_stage_running(stage)
    try:
        mod = importlib.import_module(f'worker.stages.{stage}.run')
        result = mod.run(ctx, options)
        state.set_stage_result(stage, result)
        return result
    except Exception as e:
        state.set_stage_failed(stage, str(e))
        raise
    finally:
        set_debug_log(None)


def ensure_input_video(ctx: ProjectContext, options: dict):
    """The video is downloaded by the Tauri/Rust backend, not by the worker.

    It must already live in {input}/src.f616.mp4. For CLI runs a --video
    path can be provided and is copied into place.
    """
    v = ctx.source / 'src.f616.mp4'
    if v.exists() and v.stat().st_size > 0:
        return

    provided = options.get('video')
    if not provided:
        raise RuntimeError(
            f'no source video at {v} — download it before running the worker '
            '(the Tauri backend is responsible for downloading)'
        )
    src = Path(provided)
    if not src.exists():
        raise RuntimeError(f'--video path does not exist: {src}')
    shutil.copy2(src, v)


def run_pipeline(project_id: str, options: dict, on_progress=None) -> dict:
    """Run all stages sequentially, resuming cached stages. Returns dict of results per stage."""
    ctx = ProjectContext(project_id, get_settings())
    state = ProjectState(ctx)
    state.set_options(options)
    ensure_input_video(ctx, options)

    results = {}
    total = len(STAGES)

    for i, stage in enumerate(STAGES, 1):
        print(f'[{i}/{total}] {stage}')
        if on_progress:
            on_progress(stage, i, total, 'running')

        if state.stage_current(stage):
            results[stage] = ctx.load_stage_result(stage) or {}
            print(f'  cached: {results[stage]}')
            if on_progress:
                on_progress(stage, i, total, 'done')
            continue

        if stage in ('adapt', 'separate', 'tts', 'mix'):
            transcribe_res = ctx.load_stage_result('transcribe') or {}
            if transcribe_res.get('segments', 0) == 0:
                print(f"  skipping {stage} (no speech detected)")
                skip_result = {'skipped': True}
                if stage == 'mix':
                    dl_res = ctx.load_stage_result('download') or {}
                    audio_src = ctx.transcript / dl_res.get('audio', 'dictator_hq.wav')
                    mix_out = ctx.tracks / 'mix_mastered.wav'
                    shutil.copy2(audio_src, mix_out)
                    skip_result = {'skipped': True, 'mix': 'mix_mastered.wav'}
                results[stage] = skip_result
                state.set_stage_skipped(stage, skip_result)
                if on_progress:
                    on_progress(stage, i, total, 'done')
                continue

        result = run_stage(ctx, state, stage, options)
        results[stage] = result
        print(f'  done: {result}')

        if on_progress:
            on_progress(stage, i, total, 'done')

    state.set_done()

    final = ctx.final / 'final_video.mp4'
    if final.exists():
        print(f'\nResult: {final} ({round(final.stat().st_size / 1e6, 1)} MB)')
    return results


def main():
    ap = argparse.ArgumentParser(description='Revoice Worker')
    ap.add_argument('--project', help='project id (auto-generated if omitted)')
    ap.add_argument('--video', help='path to an already-downloaded video file')
    ap.add_argument('--stage', choices=STAGES, help='run single stage')
    ap.add_argument('--voice', help='Fish Audio voice id')
    ap.add_argument('--lang', default='ru', help='target language (default: ru)')
    ap.add_argument('--uniquify', action='store_true', help='apply visual noise/eq to bypass duplication checks')
    ap.add_argument('--subtitles', action='store_true', help='burn translated subtitles into the video')
    ap.add_argument('--keep-memes', action='store_true', help='do not translate iconic quotes/memes')
    args = ap.parse_args()

    if not args.project:
        ap.print_help()
        sys.exit(2)

    options = {
        'adapt_tts': True,
        'video': args.video,
        'target_lang': args.lang,
    }
    if args.voice:
        options['voice_id'] = args.voice
    if args.uniquify:
        options['uniquify'] = True
    if args.subtitles:
        options['subtitles'] = True
    if args.keep_memes:
        options['keep_memes'] = True

    if args.stage:
        ctx = ProjectContext(args.project, get_settings())
        state = ProjectState(ctx)
        result = run_stage(ctx, state, args.stage, options)
        print(result)
    else:
        run_pipeline(args.project, options)


if __name__ == '__main__':
    main()