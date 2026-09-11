# Emberwish development policy

Follow AI-Native Development Practice. Read README.md, docs/STATUS.md,
docs/ARCHITECTURE.md and docs/VERIFICATION.md, then inspect the actual branch,
HEAD, worktree and CI evidence before changing anything. Project documents are
handoff information, not permission to execute a stored next action.

## Scope and operation

- Standalone Windows-first visual desktop toy; manual incense, wish, smoke, persistence and a recoverable widget. No shell, deployment, account, AI runtime or network integrations.
- Choose tools for product fit and AI-verifiable execution, not the owner's familiarity.
- Execute the authorized assignment phase by phase. Commit coherent rollback boundaries, not each file/edit. The MVP is developed on `feat/emberwish-mvp`; maintenance may use a separate branch/PR targeting it. Do not merge the MVP into main before required verification and independent fresh review. Prefer squash when an authorized merge happens.
- Continue only independent executable work in the authorized assignment. Findings outside it are proposals, not automatic roadmap expansion. Genuine native/runtime/reviewer blocks remain visible; they do not become implicit waivers.
- Browser evidence is not Windows/WebView2/OS evidence. A binary build is not startup, tray, input-routing, DPI or power-use verification.
- Missing, failed, blocked and stale product checks never count as passed. Re-run affected verification after meaningful source changes. Preserve exact tested revisions and artifact identities.
- Keep product status, important decisions and unresolved limitations in ordinary docs or PRs. Never store secrets or private chat transcripts.

## Tool-independent handoff

Optional execution tracking belongs outside the checkout. This repository must build,
test and be understandable without an agent's private SQLite database, skill package,
manifest, bootstrap hook or tracking-specific CI. Do not install a parallel project-state
framework to support a developer tool.

## Verification and release

Use the normal compiler, domain, browser, static and Windows checks in README and CI.
The product acceptance matrix in docs/VERIFICATION.md preserves the native and physical
checks that automation does not prove. Independent fresh review is still required for
MVP finalization; self-review or a static linter is not independent review. Record material
findings in the normal PR/review channel and update affected project acceptance details.

This maintenance does not authorize an MVP merge, release, signing, paid provisioning
or deployment, and must not overwrite concurrent development on the MVP branch.
