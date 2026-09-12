"""Per-project state file (project.json)."""
import hashlib
import json
import time
from pathlib import Path

STAGES = ['transcribe', 'adapt', 'separate', 'tts', 'mix', 'finalize']


def _now() -> str:
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def options_hash(options: dict | None) -> str:
    """Stable fingerprint of options so cached stages only survive unchanged options."""
    if not options:
        return 'none'
    return hashlib.sha256(
        json.dumps(options, sort_keys=True, ensure_ascii=False).encode('utf-8')
    ).hexdigest()


class ProjectState:
    def __init__(self, ctx):
        self.ctx = ctx
        self.path = ctx.root / 'project.json'
        self.data = self._load()

    def _load(self) -> dict:
        default = {
            'id': self.ctx.id,
            'status': 'queued',
            'current_stage': None,
            'created_at': _now(),
            'updated_at': _now(),
            'options': {},
            'options_hash': None,
            'stages': {s: {'status': 'queued'} for s in STAGES},
        }
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding='utf-8'))
                for k, v in default.items():
                    data.setdefault(k, v)
                data['stages'] = {**default['stages'], **data.get('stages', {})}
                return data
            except Exception:
                pass
        return default

    def _save(self):
        self.data['updated_at'] = _now()
        payload = json.dumps(self.data, ensure_ascii=False, indent=1)
        for attempt in range(5):
            try:
                self.path.write_text(payload, encoding='utf-8')
                return
            except (PermissionError, OSError):
                time.sleep(0.1)

    def set_options(self, options: dict):
        self.data['options'] = options or {}
        self.data['options_hash'] = options_hash(options)
        self._save()

    def set_stage_running(self, stage: str):
        self.data['status'] = 'running'
        self.data['current_stage'] = stage
        st = self.data['stages'].setdefault(stage, {})
        st['status'] = 'running'
        st['started'] = _now()
        st.pop('error', None)
        self._save()

    def set_stage_result(self, stage: str, result: dict):
        st = self.data['stages'].setdefault(stage, {})
        st['status'] = 'done'
        st['finished'] = _now()
        st['result'] = result
        st['opts_hash'] = self.data.get('options_hash')
        self._save()

    def set_stage_skipped(self, stage: str, result: dict):
        st = self.data['stages'].setdefault(stage, {})
        st['status'] = 'skipped'
        st['finished'] = _now()
        st['result'] = result
        st['opts_hash'] = self.data.get('options_hash')
        self._save()

    def stage_current(self, stage: str) -> bool:
        """True if the stage already produced a result under the current options."""
        st = self.data['stages'].get(stage) or {}
        if st.get('status') not in ('done', 'skipped'):
            return False
        return st.get('opts_hash') == self.data.get('options_hash')

    def set_stage_failed(self, stage: str, error: str):
        st = self.data['stages'].setdefault(stage, {})
        st['status'] = 'failed'
        st['finished'] = _now()
        st['error'] = str(error)[:500]
        self.data['status'] = 'failed'
        self.data['current_stage'] = stage
        self._save()

    def set_done(self):
        self.data['status'] = 'done'
        self.data['current_stage'] = None
        self._save()