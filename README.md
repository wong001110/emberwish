# Emberwish

**A tiny desktop ritual app.** Light incense, make a wish, and let it burn quietly while you work.

> For peaceful desktops and uneventful deployments.

Emberwish is a local-first, Windows-first desktop toy. It does not improve deployment success rates, run commands, read repositories, call AI models, or send your wishes to a server.

## The ritual

Write an optional wish, choose a 5-, 15- or 30-minute incense stick, and light it. A jade bowl, ember and procedural smoke provide a quiet visual companion. Extinguish it early or let it finish. Burning follows elapsed time, including while hidden or after a restart.

Expanded mode holds the ritual controls; compact mode leaves a transparent widget. In the desktop app, drag the bowl, pin the window, or hide it to the system tray. **Show & interact** in the tray clears click-through and recovers the window. Soft chimes are off by default; reduced-motion settings are respected.

## Status

This is an **MVP development build**, not a finalized or signed release. See [development status](docs/STATUS.md) for exact verified commits and remaining requirements. Browser tests, Windows WebView2 integration, OS input-routing checks and physical-machine profiling are distinct evidence levels. Do not interpret a green build as full desktop acceptance.

## Run a browser preview

Requires Node.js 22.12+ and npm. Python 3.11+ is used by the browser, native and source-evidence test tools; no private agent state is needed.

```sh
npm ci
npm run dev
```

The preview has the real scene and domain logic but uses browser localStorage. Native tray, window and application-data operations are only present in the desktop build.

## Run the desktop app on Windows

Install the Tauri 2 prerequisites: Rust, Microsoft C++ Build Tools and WebView2. Then:

```sh
npm ci
npm run desktop:dev
```

To generate a local installer:

```sh
npm run desktop:build
```

Locally generated packages are unsigned unless signing is separately configured. Do not disable operating-system security protections to install a build.

## Verify

```sh
npm run typecheck
npm test
python -m unittest discover -s tests -p 'test_workspace_evidence.py'
python tests/static_checks.py
npm run build
pip install -r requirements-dev.txt
python -m playwright install chromium
npm run test:browser
```

Set `EMBERWISH_WEB_ROOT=dist` to test the production build. Without it, the browser test compiles an explicitly labelled offline TypeScript preview. Native tests are intentionally restricted to disposable Windows CI sessions so they cannot overwrite a personal ritual.

## Development practice and architecture

Read [AGENTS.md](AGENTS.md) and the ordinary status, architecture and verification documents. The repo follows AI-Native Development Practice; optional execution trackers stay outside the checkout and are not build or CI prerequisites. Independent fresh review remains required before MVP finalization; self-review is not a substitute.

Tauri 2 + TypeScript + Vite + Canvas 2D. No React, backend, database, runtime AI, remote assets or telemetry. Canvas is a deliberate small-scene choice; the renderer boundary can support a richer engine later without changing the domain model. See [architecture](docs/ARCHITECTURE.md) and [verification](docs/VERIFICATION.md).
