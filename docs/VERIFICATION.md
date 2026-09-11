# Verification levels

1. `npm run typecheck` and `npm test`: real compiler/domain tests, no browser or native claims.
2. `npm run build:offline` then `npm run test:browser`: the same source compiled by TypeScript, served locally; tests click controls, reload storage and inspect the rendered canvas. This is not a Vite production build.
3. `npm run build`: real dependency-installed Vite production build.
4. Windows CI: native compilation, tests and a startup smoke. Producing an executable alone does not prove overlay behavior.
5. Dedicated Windows interactive test: verify an underlay receives real clicks, tray recovery, restart persistence, changed-monitor placement and target resource profile.
6. Independent fresh review with material findings dispositioned before the MVP's final merge.

Required checks remain pending/blocked until corresponding current-source evidence is obtained. Software-rendered Chromium results must not be used as Windows GPU/power measurements. These are product requirements, independent of any developer task tracker.

## Product acceptance preserved from the MVP scope

The historical IDs are retained for traceability, not as a new task database or mandatory machine-readable manifest. This table describes acceptance, not a claim that every row passed.

| Historical check | Required evidence/behavior |
|---|---|
| C-ENV-01 | TypeScript compiler and core tests execute. |
| C-ENV-02 | Production Vite build succeeds with locked dependencies. |
| C-ENV-03 | Windows native build and actual startup succeed. |
| C-CORE-01 | Light, burn, extinguish and finish use elapsed wall time. |
| C-CORE-02 | Browser can set a wish, light incense and observe real rendering changes. |
| C-SAVE-01 | Malformed, future or oversized stored values cannot corrupt the ritual. |
| C-SAVE-02 | Browser reload restores the correct burning session. |
| C-SAVE-03 | Native file persistence survives an app restart. |
| C-SAVE-04 | Consecutive/overlapping saves preserve the newest snapshot; failures are visible and retryable. |
| C-DESK-01 | Compact/expanded layout, drag, pin, hide, tray recovery and quit work in native execution. |
| C-DESK-02 | A real pointer reaches an underlay through the widget; tray interaction restores interactivity. |
| C-DESK-03 | Changed monitor/DPI layouts leave the window recoverable. |
| C-SAFE-01 | No remote assets, arbitrary shell/filesystem access, secrets or deployment integration. |
| C-SAFE-02 | Native invalid input is rejected and writes are bounded/serialized. |
| C-PERF-01 | Idle/hidden scenes stop continuous drawing and reduced motion is respected. |
| C-PERF-02 | Target-machine CPU/memory measurements distinguish physical and software-rendered environments. |
| C-A11Y-01 | Keyboard controls, focus, accessible labels and responsive layouts work. |
| C-TEST-01 | Commands and evidence limits are documented accurately. |
| C-REVIEW-01 | Independent reviewer inspects the current implementation and material findings are dispositioned. |

C-AC-01/C-AC-02 tested only the former developer tracking system. They are removed from product acceptance, not silently marked as successful product checks. Visual-only operation, elapsed-time burning, recoverable window behavior and bounded local persistence remain invariant requirements.

## Current automated native coverage

`tests/native_webdriver.py` uses the actual Tauri executable and WebView2 through `tauri-driver`. It exercises native initialization, user-triggered lighting, the Rust file store, invalid-input rejection, compact sizing, pin commands, hide/render suspension, second-instance recovery, and process-restart persistence. It does not mock `window.__TAURI__`.

Its successful command result does not independently establish that a real pointer clicked a tray menu, that a lower desktop window received a click, that monitor hotplug/DPI transitions behaved correctly, or that power consumption is acceptable on a physical machine. Those checks stay incomplete until dedicated evidence exists.

## Evidence identity

`tools/workspace_evidence.py` exports tracked source bytes, per-file SHA-256, aggregate source SHA-256, commit/tree identifiers and dirty status, without a task-store dependency. Fixture tests run with `python -m unittest discover -s tests -p 'test_workspace_evidence.py'`. They check export behavior, not desktop functionality.

The source ZIP contains no ignored/untracked files or environment values. CI artifacts/screenshots can expire; retain exact run references and meaningful results in ordinary project docs or PRs. Historical records remain at [the pre-maintenance revision](https://github.com/wong001110/emberwish/tree/4bbb187956f075579497c54bcf607de865d2346a/.agent-continuity). That reference archive is not a self-contained backup or current verification.

Do not finalize the MVP until native OS/profile/reviewer requirements have actual evidence. Removing a bookkeeping gate is not a waiver, and this maintenance is not approval to merge or release the product.
