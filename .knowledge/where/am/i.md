---
status: "unverified"
updated_at: "2026-09-20T00:12:35+10:00"
---
Status: Green

Kestrel is a programmable digital effects pedal combining an ESP32-P4 control/UI processor, Gowin FPGA audio DSP core, and KiCad PCB. This superproject owns cross-component contracts, hardware overview, and example .eff effects. The three Git submodules are kestrel_interface, kestrel_core and kestrel_pcb; the first two own separate local trees. The authored docs/eff_guide.html explains effect descriptors.

Read `what/is/the/boundary/of/the/current/specification.md` before treating current code or README ambitions as a complete future spec. Cross-component numeric command, request and opcode contracts are in `how/do/interface/and/core/numeric/protocols/align.md`. The `what/` branch covers identity, hardware, descriptor and current state; `how/` covers end-to-end flow and protocol. For implementation details, enter the owning subproject tree. The user intends a later spec workshop; unwritten ideas are not inferable facts.
