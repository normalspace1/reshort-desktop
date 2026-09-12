import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from worker.context import ProjectContext, ff, ff_bin_dir


def _copy_local_model(src_mdx: Path, ctx: ProjectContext):
    if not ctx.mdx_models.joinpath(ctx.settings.sep_model_file).exists():
        shutil.copy2(src_mdx / ctx.settings.sep_model_file, ctx.mdx_models / ctx.settings.sep_model_file)


def _find_model_dir(ctx: ProjectContext, options: dict) -> Path:
    """Locate the UVR model dir without requiring options['mdx_models'].

    Resolution order:
      1. explicit options['mdx_models'] (legacy)
      2. shared storage/models (copy model there if we can find one further down)
      3. any project under storage/projects/*/04_tracks/mdx_models that has it
    """
    name = ctx.settings.sep_model_file
    if options.get('mdx_models'):
        return Path(options['mdx_models'])

    shared = ctx.settings.models_root
    shared.mkdir(parents=True, exist_ok=True)
    if (shared / name).exists():
        return shared

    for proj in sorted(ctx.settings.projects_root.iterdir()):
        cand = proj / 'temp' / 'mdx_models'
        if cand.joinpath(name).exists():
            shutil.copy2(cand / name, shared / name)   # prime the shared cache
            return shared
    
    # If not found, return shared so audio-separator downloads it directly there
    return shared


def stem_mean_db(path: Path) -> float | None:
    r = subprocess.run([ff(), '-i', str(path), '-af', 'volumedetect', '-f', 'null', '-'],
                       capture_output=True, text=True)
    for ln in (r.stderr or '').splitlines():
        if 'mean_volume' in ln:
            return float(ln.split(':')[-1].strip().replace(' dB', ''))
    return None


def run(ctx: ProjectContext, options: dict) -> dict:
    # audio-separator calls plain 'ffmpeg' from PATH; expose our ffmpeg bin
    import os
    bin_dir = str(ff_bin_dir())
    os.environ['PATH'] = bin_dir + os.pathsep + os.environ.get('PATH', '')

    from audio_separator.separator import Separator

    src_mdx = _find_model_dir(ctx, options)

    separator = Separator(
        log_level=30,
        model_file_dir=str(src_mdx),
        output_dir=str(ctx.stems),
        output_format='WAV')
    separator.load_model(ctx.settings.sep_model_file)
    sources = separator.separate(str(ctx.transcript / 'dictator_hq.wav'))

    inst_file = next((s for s in sources if 'Instrumental' in s), sources[0] if sources else None)
    bed_file = ctx.stems / inst_file if inst_file else None
    if bed_file and not bed_file.exists():
        bed_file = ctx.stems / (sources[0] if False else 'dictator_(Instrumental).wav')
    if not bed_file or not bed_file.exists():
        # pick the single stem we produced
        cands = list(ctx.stems.glob('*Instrumental*.wav')) + list(ctx.stems.glob('*_(Instrumental)_*.wav'))
        if not cands:
            raise RuntimeError(f'no instrumental stem produced from {sources}')
        bed_file = cands[0]

    # Find the clean vocals and copy to dataset/ folder for dataset collection
    vocal_cands = list(ctx.stems.glob('*Vocals*.wav'))
    if vocal_cands:
        shutil.copy2(vocal_cands[0], ctx.transcript / 'vocals_clean.wav')

    stem_db = stem_mean_db(bed_file)
    result = {'stem': bed_file.name, 'stem_mean_db': stem_db}
    ctx.save_stage_result('separate', result)
    return result