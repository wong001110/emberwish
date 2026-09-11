# Architecture and decisions

## ADR-001: a visual toy, not a deployment agent

Manual rituals work with no IDE, login, repository, credentials, network or AI model. A ritual does not affect real deployment results. Native privileges are restricted to this app's window, tray and bounded application-data file.

## ADR-002: testable scene first, native shell kept separate

Tauri 2 + TypeScript + Vite is retained. For the first scene, use native Canvas 2D behind a renderer boundary, not PixiJS. A single fixed-view bowl and a bounded set of smoke curves do not yet require a scene-graph engine. This removes a runtime dependency and lets the exact TypeScript scene execute in an offline browser, without pretending that a mocked PixiJS renderer was verified. Revisit PixiJS only if richer scene composition warrants it.

This is a scope-preserving technical decision, not a change from desktop app to website. The browser is a preview/test adapter; Tauri remains the product shell.

Domain state has no DOM/native imports. The renderer consumes a time-derived snapshot, caps resolution/FPS, and stops continuous drawing when idle/hidden or reduced-motion is requested. Browser localStorage and the desktop application-data file implement the same bounded state format. Wall-clock timestamps determine elapsed burn time, including while hidden or after restart.

## ADR-003: execution tooling is outside the product repository

Supersedes the earlier decision to keep a developer's JSON task store and ledger on the development branch. The repository follows AI-Native Development Practice through normal product documents, Git, tests and review. Optional agent task tracking and its SQLite/snapshots/helpers belong to the execution environment, outside the checkout. No database is embedded in the product, and no private agent state is a build, test or handoff prerequisite.

Preserve ordinary product requirements, decisions and unresolved limitations here and in the PR. Do not overwrite concurrent branch updates. Historical developer-tool records remain in Git history; they are not current authority or a substitute for product evidence.

## ADR-004: explicit native boundaries

Browser effects do not verify native transparency, hit testing, tray recovery, multi-monitor placement or target-machine resource consumption. CI and dedicated native tests are separate checks. An unavailable independent reviewer blocks MVP final review/merge; it does not justify fabricating a review.

## ADR-005: reproducible evidence handoff

Enforce LF source endings through `.gitattributes`. CI exports exact tracked source bytes, per-file SHA-256 hashes, an aggregate source digest, commit/tree identity and dirty-worktree status through `tools/workspace_evidence.py`. This utility has no dependency on an agent task store. Ignored/untracked files and environment values are not included in its source ZIP.

Verify downloaded bytes against their manifest before associating test results. A source identity export proves what was captured, not that tests passed or that a dirty worktree equals HEAD. The v2 export has no scope hash and must not be confused with historical tool-specific fingerprints. Evidence remains tied to its actual tested revision; later changes require relevant re-verification rather than rewriting old evidence to match a new head.
