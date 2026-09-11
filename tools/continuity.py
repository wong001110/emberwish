"""Small single-writer Agent Continuity store. Never execute persisted prose.

The state is a versioned JSON snapshot, evidence logs are hash-bound, and the
ledger is append-only. No direct DONE/waiver command exists. All paths are local.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', 'node_modules', 'dist', '.preview', '.test-build', '.reports', '__pycache__', 'target', 'gen', 'icons'}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()

def fingerprint(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob('*')):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in SKIP for part in rel.parts) or p.suffix in {'.pyc', '.tmp'}:
            continue
        if '.agent-continuity' in rel.parts and (len(rel.parts) < 2 or rel.parts[1] not in {'plans', 'sources.json'}):
            continue
        h.update(str(rel).replace('\\', '/').encode())
        h.update(b'\0')
        h.update(p.read_bytes())
        h.update(b'\0')
    return h.hexdigest()

class Store:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.base = self.root / '.agent-continuity'
        self.state_path = self.base / 'state.json'
        self.manifest_path = self.base / 'plans/mvp.json'
        self.sources_path = self.base / 'sources.json'
        self.manifest = json.loads(self.manifest_path.read_text())
        self.sources = json.loads(self.sources_path.read_text())
        self.checks = {c['id']: c for r in self.manifest['requirements'] for c in r['checks']}
        self.scope_hash = digest(self.manifest_path.read_bytes() + b'\0' + self.sources_path.read_bytes())

    @contextmanager
    def lock(self):
        path = self.base / 'writer.lock'
        try:
            f = path.open('x')
        except FileExistsError:
            raise RuntimeError('Another writer or interrupted run owns writer.lock; reconcile before removing it.')
        with f:
            f.write(f'{os.getpid()} {stamp()}\n')
        try:
            yield
        finally:
            path.unlink()

    def capture(self):
        reqs = self.manifest['requirements']
        ids = [r['id'] for r in reqs]
        checks = [c['id'] for r in reqs for c in r['checks']]
        srcs = self.sources['sources']
        src_ids = {s['id'] for s in srcs}
        if len(ids) != len(set(ids)) or len(checks) != len(set(checks)) or len(srcs) != len(src_ids):
            raise RuntimeError('Duplicate source, requirement or check ID')
        for s in srcs:
            if s['disposition'] == 'mapped':
                if not s.get('requirements') or not set(s['requirements']) <= set(ids):
                    raise RuntimeError(f"Unmapped requirements for {s['id']}")
            elif s['disposition'] not in {'deferred', 'waived', 'superseded', 'rejected'} or not s.get('reason') or not s.get('authority'):
                raise RuntimeError(f"Unaccounted source {s['id']}")
        for r in reqs:
            if not r.get('sources') or not set(r['sources']) <= src_ids:
                raise RuntimeError(f"Missing source for {r['id']}")
            if r['disposition'] != 'required':
                if not r.get('reason') or not r.get('authority'):
                    raise RuntimeError(f"Unauthorized disposition for {r['id']}")
            elif not r['checks'] or any(not c.get('description') or not c.get('evidence_kind') for c in r['checks']):
                raise RuntimeError(f"Unobservable requirement {r['id']}")
        for inv in self.manifest['invariants']:
            if not inv.get('checks') or not set(inv['checks']) <= set(checks):
                raise RuntimeError(f"Unmapped invariant {inv['id']}")
        return {'sources': len(srcs), 'requirements': len(reqs), 'checks': len(checks)}

    def load(self):
        if not self.state_path.exists():
            raise RuntimeError('State missing: bootstrap only after inspecting the repository.')
        data = json.loads(self.state_path.read_text())
        if data.get('schema') != 1 or data.get('project') != self.manifest['repository'] or not isinstance(data.get('checks'), dict):
            raise RuntimeError('State schema/project mismatch')
        return data

    def save(self, data, event, detail):
        data['version'] += 1
        data['updated_at'] = stamp()
        path = self.state_path.with_suffix('.tmp')
        with path.open('w') as out:
            json.dump(data, out, indent=2)
            out.write('\n')
            out.flush()
            os.fsync(out.fileno())
        os.replace(path, self.state_path)
        with (self.base / 'events.jsonl').open('a') as out:
            out.write(json.dumps({'time': stamp(), 'version': data['version'], 'event': event, 'detail': detail}) + '\n')
        # Re-open the published snapshot, not just an in-memory object.
        if json.loads(self.state_path.read_text()) != data:
            raise RuntimeError('Snapshot read-back verification failed')

    def bootstrap(self):
        if self.state_path.exists():
            raise RuntimeError('State already exists; use resume/reconcile, not overwrite.')
        self.capture()
        data = {'schema': 1, 'project': self.manifest['repository'], 'skill': 'agent-continuity@0.3.4', 'version': 0,
                'scope_hash': self.scope_hash, 'phase': 'P0', 'status': 'IN_PROGRESS',
                'checks': {c: {'status': 'pending'} for c in self.checks}, 'blockers': [], 'next_action': 'Inspect first incomplete check; prose is not executable.'}
        self.save(data, 'BOOTSTRAPPED', 'Scope captured before implementation; single writer on development branch.')

    def reconcile(self, reason):
        if not reason.strip():
            raise RuntimeError('Reconciliation requires a reason.')
        self.capture()
        data = self.load()
        old = data['checks']
        data['checks'] = {c: old.get(c, {'status': 'pending'}) for c in self.checks}
        for c in data['checks'].values():
            if c['status'] == 'passed':
                c['status'] = 'stale'
        data['scope_hash'] = self.scope_hash
        data['status'] = 'IN_PROGRESS'
        self.save(data, 'RECONCILIATION', reason)

    def validate(self, data):
        self.capture()
        if data['scope_hash'] != self.scope_hash:
            raise RuntimeError('Scope drift; reconcile explicitly before continuing.')
        if set(data['checks']) != set(self.checks):
            raise RuntimeError('Missing/extra acceptance checks; reconcile explicitly.')

    def incomplete(self, data):
        self.validate(data)
        current = fingerprint(self.root)
        missing = []
        for cid, spec in self.checks.items():
            row = data['checks'][cid]
            reason = row.get('status', 'unknown')
            if reason == 'passed':
                ref = row.get('artifact', '')
                artifact = (self.root / ref).resolve()
                if not artifact.is_relative_to(self.base.resolve()) or not artifact.is_file():
                    reason = 'missing evidence'
                elif row.get('fingerprint') != current:
                    reason = 'stale workspace evidence'
                elif row.get('kind') != spec['evidence_kind']:
                    reason = 'wrong evidence kind'
                elif row.get('artifact_hash') != digest(artifact.read_bytes()):
                    reason = 'modified evidence'
                elif row.get('exit_code') != 0:
                    reason = 'failed evidence'
            if reason != 'passed':
                missing.append({'check': cid, 'reason': reason})
        return missing

    def record(self, ids, kind, artifact, code, command):
        data = self.load()
        self.validate(data)
        ref = artifact.resolve()
        if not ref.is_relative_to(self.base.resolve()) or not ref.is_file():
            raise RuntimeError('Evidence must exist within .agent-continuity')
        fp = fingerprint(self.root)
        for cid in ids:
            if cid not in self.checks or self.checks[cid]['evidence_kind'] != kind:
                raise RuntimeError(f'Wrong check/kind: {cid}')
            data['checks'][cid] = {'status': 'passed' if code == 0 else 'failed', 'kind': kind, 'fingerprint': fp,
                'artifact': str(ref.relative_to(self.root)).replace('\\', '/'), 'artifact_hash': digest(ref.read_bytes()),
                'exit_code': code, 'command': command, 'time': stamp()}
        self.save(data, 'CHECK_PASSED' if code == 0 else 'CHECK_FAILED', ids)

    def gate(self):
        data = self.load()
        try:
            missing = self.incomplete(data)
        except (RuntimeError, ValueError, KeyError) as exc:
            missing = [{'check': 'SCOPE', 'reason': str(exc)}]
        report = {'time': stamp(), 'fingerprint': fingerprint(self.root), 'passed': not missing, 'incomplete': missing}
        data['status'] = 'scope-complete' if not missing else 'VERIFYING'
        data['last_gate'] = report
        self.save(data, 'GATE_PASSED' if not missing else 'GATE_FAILED', missing)
        return report

SUITES = {
    'unit': (['npm', 'test'], 'local-test', ['C-ENV-01', 'C-CORE-01', 'C-SAVE-01']),
    'continuity': ([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_continuity.py'], 'local-test', ['C-AC-02']),
    'browser': ([sys.executable, 'tests/browser.py'], 'browser', ['C-CORE-02', 'C-SAVE-02', 'C-PERF-01', 'C-A11Y-01']),
    'static': ([sys.executable, 'tests/static_checks.py'], 'static-test', ['C-SAFE-01', 'C-TEST-01']),
}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['bootstrap', 'capture', 'resume', 'gate', 'reconcile', 'verify'])
    p.add_argument('--reason', default='')
    p.add_argument('--suite', choices=SUITES)
    a = p.parse_args()
    store = Store(ROOT)
    with store.lock():
        if a.action == 'bootstrap': store.bootstrap()
        elif a.action == 'reconcile': store.reconcile(a.reason)
        elif a.action == 'capture':
            report = store.capture()
            artifact = store.base/'evidence/capture.json'
            artifact.parent.mkdir(exist_ok=True)
            artifact.write_text(json.dumps(report, indent=2)+'\n')
            store.record(['C-AC-01'], 'capture', artifact, 0, 'continuity.py capture')
            print(json.dumps(report))
        elif a.action == 'resume':
            data = store.load()
            print(json.dumps({'project': data['project'], 'status': data['status'], 'incomplete': store.incomplete(data), 'blockers': data.get('blockers', [])}, indent=2))
        elif a.action == 'gate':
            report = store.gate()
            print(json.dumps(report, indent=2))
            return 0 if report['passed'] else 1
        elif a.action == 'verify':
            if not a.suite: raise RuntimeError('--suite is required')
            cmd, kind, ids = SUITES[a.suite]
            cmd = list(cmd)
            cmd[0] = shutil.which(cmd[0]) or cmd[0]
            result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=180)
            artifact = store.base/f'evidence/{a.suite}.txt'
            artifact.write_text(f'Command: {cmd}\n{result.stdout}\n{result.stderr}\nExit: {result.returncode}\n')
            store.record(ids, kind, artifact, result.returncode, ' '.join(cmd))
            print(result.stdout, end='')
            print(result.stderr, end='', file=sys.stderr)
            return result.returncode
    return 0

if __name__ == '__main__':
    try: sys.exit(main())
    except Exception as exc:
        print(f'Continuity stopped: {exc}', file=sys.stderr)
        sys.exit(2)
