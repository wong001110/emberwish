"""Compile the real source for an offline preview, without pretending this is Vite."""
from pathlib import Path
import shutil
import subprocess
ROOT = Path(__file__).resolve().parents[1]
subprocess.run([shutil.which('tsc') or 'tsc', '-p', 'tsconfig.json'], cwd=ROOT, check=True)
out = ROOT / '.preview'
out.mkdir(exist_ok=True)
(out / 'index.html').write_text((ROOT / 'index.html').read_text().replace('/src/main.ts', '/src/main.js'))
for item in (ROOT / 'src').glob('*.css'):
    shutil.copy2(item, out / 'src' / item.name)
print('Offline source preview compiled; not a production/native build.')
