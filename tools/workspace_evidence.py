"""Export the exact checked-out public source and its identity for offline review.

No secrets/environment values or ignored/untracked files are included in the ZIP.
The ZIP is verification material, not a substitute for the canonical Git branch.
"""
from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess
import zipfile
from continuity import Store, fingerprint
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.reports';OUT.mkdir(exist_ok=True)
def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()
commit=git('rev-parse','HEAD')
paths=git('ls-files','-z').split('\0')
files={}
with zipfile.ZipFile(OUT/'workspace.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for path in paths:
        if not path:continue
        p=ROOT/path
        if p.is_symlink() or not p.resolve().is_relative_to(ROOT) or not p.is_file():
            raise RuntimeError('Unexpected tracked source path: '+path)
        if p.name=='.env' or p.name.startswith('.env.'):
            raise RuntimeError('Environment files must not be tracked in the evidence export')
        archive.write(p,path)
        files[path]=hashlib.sha256(p.read_bytes()).hexdigest()
store=Store(ROOT)
identity={'commit':commit,'tree':git('rev-parse','HEAD^{tree}'),
          'fingerprint':fingerprint(ROOT),'scope_hash':store.scope_hash,
          'platform':platform.platform(),'run_id':os.getenv('GITHUB_RUN_ID'),
          'files':files,'note':'Source identity only. Actual test outcomes come from the CI job logs and browser/native reports.'}
(OUT/'workspace.json').write_text(json.dumps(identity,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in identity.items() if k!='files'}))
