# Development status (derived view)

P0 baseline compile/startup passed in Actions 34570876253 for ff99cbd. P1 passed production browser tests and Windows compile/startup in Actions 34572166738 for 1672086. JavaScript and Rust dependency locks were captured in one follow-up commit 3143b4d.

P1: manual light/extinguish/finish, wishes, 5/15/30-minute burns, original Canvas bowl/smoke, browser persistence, silent-by-default chime, reduced motion and expanded/compact layouts. The local 28 Node tests and 15 continuity tests passed; the production browser suite passed on GitHub CI, not in the locally restricted browser.

P2 implementation: app-owned bounded/atomic native storage, input validation, transparent compact window, monitor-aware expanded sizing, canvas dragging, pin/hide, tray recovery, safe quit flushing and single-instance recovery. Six Rust storage tests and real Windows WebDriver coverage are included. These new native changes must pass their own CI before acceptance.

Known findings FND-001..004 are mapped, with fixes and regression paths. Full native tray pointer interaction, real underlay click-through, changed monitor/DPI behavior, physical-machine profiling and independent fresh review still require evidence. No claim of a finalized release or complete desktop validation is made.

Local browser navigation is administratively blocked and was not bypassed. Offline visual fixtures were explicitly mocked for storage; they are not accepted persistence/native evidence. Use CI artifacts for actual production browser/native outputs.
