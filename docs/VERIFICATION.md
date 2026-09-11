# Verification levels

1. `npm run typecheck` and `npm test`: real compiler/domain tests, no browser or native claims.
2. `npm run build:offline` then `npm run test:browser`: the same source compiled by TypeScript, served locally; tests click controls, reload storage and inspect the rendered canvas. This is not a Vite production build.
3. `npm run build`: real dependency-installed Vite production build.
4. Windows CI: native compilation, tests and a startup smoke. Producing an executable alone does not prove overlay behavior.
5. Dedicated Windows interactive test: verify an underlay receives real clicks, tray recovery, restart persistence, changed-monitor placement and target resource profile.
6. Independent fresh review and source/finding disposition before final merge.

Required checks remain pending/blocked until their corresponding evidence is obtained. Software-rendered Chromium results must not be used as Windows GPU/power measurements.
