"""Small explicit invariants, not a substitute for an independent code review."""
from pathlib import Path
import json, re
R=Path(__file__).resolve().parents[1]
html=(R/'index.html').read_text(encoding='utf-8')
assert not re.search(r'(?:src|href)=["\']https?://',html)
code='\n'.join(p.read_text(encoding='utf-8') for p in (R/'src').glob('*.ts'))
assert not re.search(r'\b(?:eval|fetch)\s*\(',code)
assert '.innerHTML' not in code
cargo=(R/'src-tauri/Cargo.toml').read_text()
for forbidden in ['tauri-plugin-shell','tauri-plugin-http','tauri-plugin-fs','reqwest']:assert forbidden not in cargo
config=json.loads((R/'src-tauri/tauri.conf.json').read_text())
assert config['app']['windows'][0]['label']=='main'
assert "default-src 'self'" in config['app']['security']['csp']
assert "object-src 'none'" in config['app']['security']['csp']
cap=json.loads((R/'src-tauri/capabilities/main.json').read_text())
assert cap['windows']==['main'];assert set(cap['permissions'])=={'core:event:allow-listen','core:event:allow-unlisten'}
for p in ['docs/ARCHITECTURE.md','docs/VERIFICATION.md','AGENTS.md']:assert (R/p).is_file()
verification=(R/'docs/VERIFICATION.md').read_text()
assert 'native' in verification and 'independent' in verification.lower()
print('PASS: local assets, text-only wish insertion, bounded native surface and explicit verification documentation')
