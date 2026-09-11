# Development status

This is the project's ordinary handoff under AI-Native Development Practice. Consult
actual source, tests and CI receipts; no agent-specific database or bootstrap is required.

## Product state at the maintenance baseline

Inspected MVP branch: `feat/emberwish-mvp`, revision
`4bbb187956f075579497c54bcf607de865d2346a`. Main is still the initial README-only
baseline. This maintenance branch does not merge or release the MVP.

P0 and P1 baseline checks were recorded as passed at their respective commits.
P2 production browser checks passed in Actions run 34573285341; the native job failed
with Rust error E0308 in storage::write_atomic. FND-007 records the correction in P3,
but correction text is not a successful compiler/test result. No run for the exact
inspected P3 head was returned during this maintenance inspection.

P3 contains 30 Node tests and native input/storage/WebView2 automation. Its former 18
tracking-tool tests were developer-tool checks, not product tests. They are no longer
part of the product's pipeline. Existing compiler/domain/browser/static/native checks
remain; source-evidence export has independent fixture tests.

No historical test result is automatically promoted to verification of this maintenance
commit. Inspect its own web and Windows CI before accepting current-source evidence.

## Implemented capabilities

Manual light/extinguish/finish, wishes, 5/15/30-minute burns, original Canvas bowl/smoke,
expanded/compact layouts, opt-in chime, reduced motion, native bounded file store,
recoverable tray, pin/hide, canvas drag, monitor-fit sizing and single-instance recovery.

## Remaining acceptance

Tray/input-underlay pointer behavior, changed monitor/DPI behavior, physical-machine
profiling and independent fresh review require separate evidence. Native P3 compiler,
startup and WebView2 results must also be confirmed on the relevant revision. None is
waived or counted complete by removing a task tracker. See docs/VERIFICATION.md.

The pre-maintenance tracking history remains at immutable Git revision
`4bbb187956f075579497c54bcf607de865d2346a`; it is historical evidence, not a current
runtime dependency or permission to continue an unrelated assignment.
