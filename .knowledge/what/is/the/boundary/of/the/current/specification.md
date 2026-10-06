---
status: green
revised_at: "2026-10-03T23:14:20+10:00"
---

The READMEs and code describe implemented and intended behaviour, but are not a complete formal product specification. David's next-revision hardware requirements are owned by what/is/the/single/board/and/enclosure/design/brief.md. They supersede carrier-module assumptions as the desired direction, not as a description of existing hardware.

David has also supplied partial firmware and RTL requirements. The Interface and Core trees' what/is/the/spec.md leaves own those component intentions, and this superproject's what/is/the/effect/verification/specification.md owns the shared automated tests, lightweight DSP simulation, one-pipeline RTL verification and physical HIL goals. They are requirements and design candidates, not claims of completed implementation.

The specification remains open: allocation boundaries, effect-refresh lifecycle, debug-command details, simulator fidelity/acceptance and DSP optimization/post-processing contracts need refinement, and further RTL intentions remain to be elicited. Ask for goals, priorities and acceptance criteria rather than promoting old README ambitions or proposed mechanisms into settled requirements.

Sources: project READMEs and David's explicit hardware and firmware/RTL instructions.
