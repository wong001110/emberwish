# Verification levels

1. `npm run typecheck` and `npm test`: real compiler/domain tests, no browser or native claims.
2. `npm run build:offline` then `npm run test:browser`: the same source compiled by TypeScript, served locally; tests click controls, reload storage and inspect the rendered canvas. This is not a Vite production build.
3. `npm run build`: real dependency-installed Vite production build.
4. Windows CI: native compilation, tests and a startup smoke. Producing an executable alone does not prove overlay behavior.
5. Dedicated Windows interactive test: verify an underlay receives real clicks, tray recovery, restart persistence, changed-monitor placement and target resource profile.
6. Independent fresh review and source/finding disposition before final merge.

Required checks remain pending/blocked until their corresponding evidence is obtained. Software-rendered Chromium results must not be used as Windows GPU/power measurements.

## Current automated native coverage

`tests/native_webdriver.py` uses the actual Tauri executable and WebView2 through `tauri-driver`. It exercises native initialization, user-triggered lighting, the Rust file store, invalid-input rejection, compact sizing, pin commands, hide/render suspension, second-instance recovery, and process-restart persistence. It does not mock `window.__TAURI__`.

Its successful command result does not independently establish that a real pointer clicked a tray menu, that a lower desktop window received a click, that monitor hotplug/DPI transitions behaved correctly, or that power consumption is acceptable on a physical machine. Those checks stay incomplete until dedicated evidence exists.

## Evidence identity

`tools/workspace_evidence.py` exports tracked source bytes, SHA-256 hashes, commit/tree identifiers and the continuity fingerprint. The source ZIP contains no ignored/untracked files or environment values. CI build artifacts and screenshots expire according to GitHub artifact retention; the branch stores durable small evidence summaries and check state, with exact CI run references.

`python tools/continuity.py gate` returns nonzero for the still-missing native OS/profile/reviewer checks. This is an expected fail-closed result during development, not permission to mark them complete. `resume` refuses a published workspace fingerprint mismatch; reconcile only after inspecting the actual change.
