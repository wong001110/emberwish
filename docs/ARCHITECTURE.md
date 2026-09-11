# Architecture and decisions

## ADR-001: a visual toy, not a deployment agent

Manual rituals work with no IDE, login, repository, credentials, network or AI model. A ritual does not affect real deployment results. Native privileges are restricted to this app's window, tray and bounded application-data file.

## ADR-002: testable scene first, native shell kept separate

Tauri 2 + TypeScript + Vite is retained. For the first scene, use native Canvas 2D behind a renderer boundary, not PixiJS. A single fixed-view bowl and a bounded set of smoke curves do not yet require a scene-graph engine. This removes a runtime dependency and lets the exact TypeScript scene execute in an offline browser, without pretending that a mocked PixiJS renderer was verified. Revisit PixiJS only if richer scene composition warrants it.

This is a scope-preserving technical decision, not a change from desktop app to website. The browser is a preview/test adapter; Tauri remains the product shell.

Domain state has no DOM/native imports. The renderer consumes a time-derived snapshot, caps resolution/FPS, and stops continuous drawing when idle/hidden or reduced-motion is requested. Browser localStorage and the desktop application-data file implement the same bounded state format. Wall-clock timestamps determine elapsed burn time, including while hidden or after restart.

## ADR-003: small sequential continuity store

Use versioned JSON snapshots plus evidence records and an append-only event ledger, owned by one writer on the development branch. The skill permits a durable store without requiring SQLite. No database is embedded in the product. Git supplies durable publication and conflict detection; the gate binds evidence to a deterministic workspace fingerprint and its actual log hash. Use a transactional DB/leases if concurrent writers are introduced. Do not overwrite concurrent branch updates.

## ADR-004: explicit native boundaries

Browser effects do not verify native transparency, hit testing, tray recovery, multi-monitor placement or target-machine resource consumption. CI and dedicated native tests are separate checks. An unavailable independent reviewer blocks final review/merge; it does not justify fabricating a review.
