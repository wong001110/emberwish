import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
test('app keeps its visual-only native boundary', () => {
  const config = JSON.parse(readFileSync('src-tauri/tauri.conf.json', 'utf8'));
  assert.equal(config.app.windows[0].label, 'main');
  assert.equal(config.app.windows[0].transparent, true);
  assert.match(config.app.security.csp, /object-src 'none'/);
});
